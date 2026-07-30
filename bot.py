import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
URL = f"https://api.telegram.org/bot{TOKEN}"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        update = request.get_json()
        if update and "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"].get("text", "")
            
            # ለቴሌግራም መልዕክት የሚሰጠው ምላሽ
            reply = f"ሰላም! መልዕክትህ ደርሶኛል: '{text}'"
            send_message(chat_id, reply)
        return "OK", 200
    return "🤖 የቴሌግራም AI ቦት በሰላም እየሰራ ነው!", 200

def send_message(chat_id, text):
    url = f"{URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
