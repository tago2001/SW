# utils/discord_notify.py
import requests
import socket

WEBHOOK_URL = "https://discord.com/api/webhooks/1407480219039694958/HH7cIr8NCZyIURnIw7EbWo_pC55VaxkrdcI6GB6e2iddMsWoH2HWDg5_R3crjvp_Edcp"

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org").text
    except Exception as e:
        return f"Error fetching public IP: {e}"

def get_local_ip():
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception as e:
        return f"Error fetching local IP: {e}"

def send_to_discord(message: str):
    try:
        response = requests.post(WEBHOOK_URL, json={"content": message})
        return response.status_code
    except Exception as e:
        return f"Error sending to Discord: {e}"

def notify_ip():
    public_ip = get_public_ip()
    local_ip = get_local_ip()
    message = f"🚀 Django app started!\n🌐 Public IP: {public_ip}\n🏠 Local IP: {local_ip}"
    return send_to_discord(message)
