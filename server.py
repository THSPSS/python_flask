from dotenv import load_dotenv
import requests
from flask import Flask, jsonify , request
import os
from datetime import datetime
from main import scan
from threading import Thread

load_dotenv()

app = Flask(__name__)

weekday_map = ['월', '화', '수', '목', '금', '토', '일']
TOKEN = os.getenv("TOKEN")

def send_to_telegram(recipient_id: str, message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": recipient_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

def scan_and_notify(recipient_id: str):
    try:
        df = scan()

        if df.empty:
            message = "❗조건을 만족하는 종목이 없습니다."
        else:
            now_time_format = datetime.now().strftime("%y-%m-%d") + f"({weekday_map[datetime.now().weekday()]})"
            message = f"📊 {now_time_format} RSI 20일 조건 종목 알림\n\n" + "\n\n".join([
                f"🔹 {row['종목명']} ({row['종목코드']})\n📈 상승률: {row['상승률%']}%\nRSI: {row['어제RSI']} > {row['최저RSI']}"
                for _, row in df.iterrows()
            ])

        send_to_telegram(recipient_id, message)

    except Exception as e:
        send_to_telegram(chat_id, f"❌ 에러 발생: {e}")


@app.route("/")
def home():
    return "✅ Flask server is running!"

@app.route("/rsi-scan", methods=["GET"])
def run_scan():
    recipient_id = request.args.get("chat_id") or request.args.get("channel_id")

    if not recipient_id:
        return jsonify({"error": "chat_id 또는 channel_id 파라미터가 필요합니다."}), 400

    # Start scan in background
    Thread(target=scan_and_notify, args=(recipient_id,)).start()

    # Return immediately
    return jsonify({"message": f"RSI 스캔을 시작했습니다. 결과는 텔레그램으로 전송됩니다. ✅"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)