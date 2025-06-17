from dotenv import load_dotenv
import requests
from flask import Flask, jsonify , request
import os
from datetime import datetime
from main import scan

load_dotenv()
app = Flask(__name__)

weekday_map = ['월', '화', '수', '목', '금', '토', '일']
TOKEN = os.getenv("TOKEN")

def send_to_telegram(chat_id: str, message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()


@app.route("/rsi-scan", methods=["GET"])
def run_scan():
    chat_id = request.args.get("chat_id")  # e.g., ?chat_id=12345678
    print(f"get chat id {chat_id}")
    #text에 따라 진행
    df = scan()

    if df.empty:
       summary = jsonify({"message": "❗조건을 만족하는 종목이 없습니다."})
    else:
        now_time_format = datetime.now().strftime("%y-%m-%d") + f"({weekday_map[datetime.now().weekday()]})"
        summary =  f"📊 {now_time_format} RSI 20일 조건 종목 알림\n\n" + "\n".join([
            f"🔹 {row['종목명']} ({row['종목코드']})\n📈 상승률: {row['상승률%']}%\nRSI: {row['어제RSI']} > {row['최저RSI']}"
            for _, row in df.iterrows()
        ])

    # If chat_id is given, send to Telegram
    if chat_id:
        try:
            send_to_telegram(chat_id, summary)
        except Exception as e:
            return jsonify({"message": "Telegram 전송 실패", "error": str(e)}), 500

    return jsonify({"message": summary})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)