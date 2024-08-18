import requests
import random
import time
from flask import Flask

# Telegram bot token and chat ID (previously provided)
BOT_TOKEN = "7195510626:AAFtR4-XWXBGvn1xy7tuUovWnWJa-LxyCWw"
CHAT_ID = "-1002163921366"

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

def send_message_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
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
            message = (f"GENERATED 𝗕𝗜𝗡 ⇾ {bin_number}\n\n"
                       f"𝗜𝗻𝗳𝗼 ⇾ {bin_info['brand']} - {bin_info['type']} - {bin_info['level']}\n"
                       f"𝐈𝐬𝐬𝐮𝐞𝐫 ⇾ {bin_info['bank']}\n"
                       f"𝐂𝐨𝐮𝐧𝐭𝐫𝐲 ⇾ {bin_info['country_name']} {bin_info['country_flag']}")
            print(message)  # Print the full 10-digit BIN
            
            if bin_info['type'] == "CREDIT":
                send_message_to_telegram(message)
            
        time.sleep(1)  # Delay to prevent overwhelming the API

@app.route('/keep_alive')
def keep_alive():
    return "Script is running."

if __name__ == '__main__':
    from threading import Thread
    
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    flask_thread.start()
    
    generate_and_send_bins()
    
