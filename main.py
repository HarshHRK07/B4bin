import requests
import random
from flask import Flask

# Telegram bot token and chat ID (previously provided)
BOT_TOKEN = "7430804194:AAFAXQru9th5FvmMwlaTfTbSLDb5TprpEt"
CHAT_ID = "6460703454"

app = Flask(__name__)

def generate_bin():
    # Randomly choose to generate either a Visa or MasterCard BIN
    prefix = random.choice(['4', '5'])  # '4' for Visa, '5' for MasterCard
    bin_number = prefix + ''.join([str(random.randint(0, 9)) for _ in range(5)])
    return bin_number

def get_bin_info(bin_number):
    url = f"https://bins.antipublic.cc/bins/{bin_number}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to retrieve BIN information"}

def send_message_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)

def generate_and_send_bins():
    while True:
        bin_number = generate_bin()
        bin_info = get_bin_info(bin_number)
        
        if "error" not in bin_info:
            # Construct the message with the BIN information
            message = (f"Generated BIN: {bin_info['bin']}\n"
                       f"Brand: {bin_info['brand']}\n"
                       f"Country: {bin_info['country_name']} ({bin_info['country_flag']})\n"
                       f"Bank: {bin_info['bank']}\n"
                       f"Level: {bin_info['level']}\n"
                       f"Type: {bin_info['type']}\n"
                       f"Currencies: {', '.join(bin_info['country_currencies'])}")
            send_message_to_telegram(message)
            
            # Check if the specific BIN is found and notify
            if (bin_info['bank'] == "BANK OF BAHRAIN AND KUWAIT" and 
                bin_info['brand'] == "MASTERCARD" and 
                bin_info['type'] == "CREDIT"):
                specific_message = ("Specific BIN Found!\n" + message)
                send_message_to_telegram(specific_message)
                print("Required BIN found and sent to Telegram!")

@app.route('/keep_alive')
def keep_alive():
    return "Script is running."

if __name__ == '__main__':
    # Start the Flask server in a separate thread
    from threading import Thread
    
    flask_thread = Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    flask_thread.start()
    
    # Start the BIN generation and sending process
    generate_and_send_bins()
        
