import os
import requests

TOKEN = os.environ.get("TELEGRAM_TOKEN")
# ወይም በቀጥታ ቶክንህን እዚህ ውስጥ ማስገባት ትችላለህ: TOKEN = "የቦትህ_ቶክን"
URL = f"https://api.telegram.org/bot{TOKEN}"

def get_updates(offset=None):
    url = f"{URL}/getUpdates?timeout=100"
    if offset:
        url += f"&offset={offset}"
    response = requests.get(url)
    return response.json()

def send_message(chat_id, text):
    url = f"{URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def main():
    print("🤖 ቦቱ በ Polling ሁነታ ስራውን ጀምሯል...")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            if "result" in updates:
                for update in updates["result"]:
                    offset = update["update_id"] + 1
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        text = update["message"]["text"]
                        
                        # ለቀረበው መልዕክት የሚሰጠው ምላሽ
                        reply = f"ሰላም! መልዕክትህ ደርሶኛል: '{text}'"
                        send_message(chat_id, reply)
        except Exception as e:
            print(f"ስህተት ተፈጥሯል: {e}")

if __name__ == "__main__":
    main()
