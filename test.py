import requests
import random
import time
import json
from flask import Flask
from threading import Thread

# Telegram bot token and chat ID
BOT_TOKEN = "7195510626:AAE4KKwNyYPM8Q0NSdTrn6gzEvZqrvz"
CHAT_ID = "-1002181591571"  # Ensure this is in the correct format for groups

app = Flask(__name__)

def generate_bin():
    prefix = random.choice(['3', '4', '5', '34', '6', '8'])  # '3' and '34' for Amex, '4' for Visa, '5' for MasterCard
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

def generate_card(bin_number):
    while True:
        card_number = bin_number + ''.join([str(random.randint(0, 9)) for _ in range(6)])
        if luhn_algorithm(card_number):
            break
    exp_month = str(random.randint(1, 12)).zfill(2)
    exp_year = str(random.randint(2025, 2030))
    cvv_length = 4 if bin_number.startswith('3') else 3
    cvv = ''.join([str(random.randint(0, 9)) for _ in range(cvv_length)])
    return f"{card_number}|{exp_month}|{exp_year}|{cvv}"

def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number[:6]}"  # First 6 digits
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching BIN info: {e}")
        return {"error": "Failed to retrieve BIN information"}

def format_bin_message(bin_number, bin_info, card_info, api_response):
    label = "CREDIT BIN" if bin_info.get('type') == "CREDIT" else "DEBIT/PREPAID BIN"
    
    message = (
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 BIN Generated: `{bin_number}`\n"
        f"💳 Card: `{card_info}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 Brand: `{bin_info.get('brand', 'N/A')}`\n"
        f"🏦 Type: {bin_info.get('type', 'N/A')} ({label})\n"
        f"⚡ Level: `{bin_info.get('level', 'N/A')}`\n"
        f"🏢 Bank: `{bin_info.get('bank', 'N/A')} 🏛️`\n"
        f"🌍 Country: `{bin_info.get('country_name', 'N/A')} {bin_info.get('country_flag', '')}`\n"
    )

    if 'error' in api_response:
        message += (
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Error Code: `{api_response['error'].get('code', 'N/A')}`\n"
            f"⚠️ Decline Code: `{api_response['error'].get('decline_code', 'N/A')}`\n"
            f"🔗 Doc URL: `{api_response['error'].get('doc_url', 'N/A')}`\n"
            "━━━━━━━━━━━━━━━━━━━━━━━"
        )
    
    return message

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
    files = {'document': open(file_path, 'rb')}
    data = {'chat_id': CHAT_ID}
    try:
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        print("File sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending file to Telegram: {e}")
    finally:
        files['document'].close()

def verify_card(card_info):
    url = "https://ugin-376ec3a40d16.herokuapp.com/cvv"
    params = {'cc': card_info}
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error verifying card: {e}")
        return {"error": "Failed to verify card"}

def generate_and_send_bins():
    while True:
        bin_number = generate_bin()
        bin_info = get_bin_info(bin_number)
        
        if "error" not in bin_info:
            card_info = generate_card(bin_number)
            api_response = verify_card(card_info)
            
            if "error" in api_response and api_response["error"] == "Failed to verify card":
                file_path = "raw_response.txt"
                with open(file_path, "w") as file:
                    file.write(json.dumps(api_response, indent=4))
                send_file_to_telegram(file_path)
            else:
                message = format_bin_message(bin_number, bin_info, card_info, api_response)
                send_message_to_telegram(message)
            
        time.sleep(2)  # Delay to prevent overwhelming the API

@app.route('/keep_alive')
def keep_alive():
    return "Script is running."

if __name__ == '__main__':
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    flask_thread.start()
    
    generate_and_send_bins()
        
