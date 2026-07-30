import logging
import requests

TELEGRAM_TOKEN = "8674508996:AAHyJSJnkdYtF4wXUdVz0ZFQXSIpjLBM59E"
OPENAI_API_KEY = "Sk-proj-UXraT9-tkojWG5WoFSMQWT4h6Yii6pNWf3ctCcsxIbyQFpha_CwAW4sqMoukT--ecYpgRPywk1T3BlbkFJ1P6iZSknmECMuuKbmP4QNTaXd6PiUGsT-5lpUb6tg2yTEoAdIRNALvAlqiUKRvC6mskZIGVukA"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def ask_openai(prompt):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are Nebiyu's smart personal AI assistant on Telegram. Reply professionally and intelligently to users in a helpful tone."},
            {"role": "user", "content": prompt}
        ]
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        res_json = response.json()
        if "choices" in res_json:
            return res_json["choices"][0]["message"]["content"]
        else:
            return "ይቅርታ፣ አሁን ከ OpenAI አገልጋይ ጋር መገናኘት አልቻልኩም።"
    except Exception as e:
        return "ይቅርታ፣ የኔትወርክ ስህተት አጋጥሟል።"

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Telegram Send Error:", e)

def main():
    print("🤖 የቴሌግራም AI ቦት በ HTTP Requests ሁነታ ስራውን ጀምሯል...")
    offset = None
    
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?timeout=30"
            if offset:
                url += f"&offset={offset}"
            
            response = requests.get(url, timeout=35)
            data = response.json()
            
            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1
                    
                    if "message" in update and "text" in update["message"]:
                        chat_id = update["message"]["chat"]["id"]
                        user_message = update["message"]["text"]
                        
                        ai_reply = ask_openai(user_message)
                        send_telegram_message(chat_id, ai_reply)
        
        except Exception as e:
            print("Polling Error:", e)

if __name__ == "__main__":
    main()
 
