import requests
import random
import time
from flask import Flask

# Telegram bot token and chat ID
BOT_TOKEN = "7430804194:AAFAXQru9th5FvmMwlaTfTbSLDb5TprpEtQ"
CHAT_ID = "6460703454"

app = Flask(__name__)

def generate_bin():
    # Generate a 10-digit BIN starting with '4' for Visa or '5' for MasterCard
    prefix = random.choice(['4', '5'])  # '4' for Visa, '5' for MasterCard
    bin_number = prefix + ''.join([str(random.randint(0, 9)) for _ in range(9)])  # Remaining 9 digits
    return bin_number

def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number[:6]}"  # Use only the first 6 digits to get BIN info
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching BIN info: {e}")
        return {"error": "Failed to retrieve BIN information"}

def format_bin_message(bin_number, bin_info):
    # Label for credit BINs
    label = "CREDIT BIN" if bin_info['type'] == "CREDIT" else "DEBIT/PREPAID BIN"
    
    return (
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔹 BIN Generated: `{bin_number}`\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💳 Brand: `{bin_info['brand']}`\n"
        f"🏦 Type: {bin_info['type']} ({label})\n"
        f"⚡ Level: `{bin_info['level']}`\n"
        f"🏢 Bank: `{bin_info['bank']} 🏛️`\n"
        f"🌍 Country: `{bin_info['country_name']} {bin_info['country_flag']}`\n"
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
        requests.post(url, data=payload)
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

def generate_and_send_bins():
    while True:
        bin_number = generate_bin()
        bin_info = get_bin_info(bin_number)
        
        if "error" not in bin_info:
            message = format_bin_message(bin_number, bin_info)
            print(message)  # Print the formatted BIN information
            
            send_message_to_telegram(message)  # Send message for all BIN types
            
        time.sleep(0.5)  # Delay to prevent overwhelming the API

@app.route('/keep_alive')
def keep_alive():
    return "Script is running."

if __name__ == '__main__':
    from threading import Thread
    
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    flask_thread.start()
    
    generate_and_send_bins()
            
