import requests
import random
import time
from flask import Flask
from threading import Thread

# Telegram bot token and chat ID
BOT_TOKEN = "7195510626:AAEyR3F9NH5cyMsEcObqCpFvkwCFrc6C9M4"
CHAT_ID = "-1002181591571"  # Ensure this is in the correct format for groups

app = Flask(__name__)

def generate_bin():
    prefix = random.choice(['3', '4', '5'])  # '4' for Visa, '5' for MasterCard
    bin_number = prefix + ''.join([str(random.randint(0, 9)) for _ in range(9)])  # 9 more digits
    return bin_number

def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number[:6]}"  # First 6 digits
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching BIN info: {e}")
        return {"error": "Failed to retrieve BIN information"}

def format_bin_message(bin_number, bin_info):
    label = "CREDIT BIN" if bin_info.get('type') == "CREDIT" else "DEBIT/PREPAID BIN"
    
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 BIN Generated: `{bin_number}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 Brand: `{bin_info.get('brand', 'N/A')}`\n"
        f"🏦 Type: {bin_info.get('type', 'N/A')} ({label})\n"
        f"⚡ Level: `{bin_info.get('level', 'N/A')}`\n"
        f"🏢 Bank: `{bin_info.get('bank', 'N/A')} 🏛️`\n"
        f"🌍 Country: `{bin_info.get('country_name', 'N/A')} {bin_info.get('country_flag', '')}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━"
    )

def send_message_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    attempt = 0
    max_attempts = 5
    while attempt < max_attempts:
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            response_data = response.json()
            if not response_data.get("ok"):
                print(f"Telegram API error: {response_data.get('description')}")
            else:
                print("Message sent successfully.")
            return
        except requests.exceptions.RequestException as e:
            if e.response.status_code == 429:  # Too Many Requests
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying...")
                time.sleep(wait_time)
                attempt += 1
            else:
                print(f"Error sending message to Telegram: {e}")
                return

def generate_and_send_bins():
    while True:
        bin_number = generate_bin()
        bin_info = get_bin_info(bin_number)
        
        if "error" not in bin_info:
            message = format_bin_message(bin_number, bin_info)
            print("Generated message to send:", message)  # Debugging line
            
            send_message_to_telegram(message)  # Send message for all BIN types
            
        time.sleep(0.5)  # Delay to prevent overwhelming the API

@app.route('/keep_alive')
def keep_alive():
    return "Script is running."

if __name__ == '__main__':
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    flask_thread.start()
    
    generate_and_send_bins()
    
