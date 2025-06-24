from dotenv import load_dotenv
import os
import requests

from scans.long_shadow_scan import long_lower_shadow_scan, format_shadow_message
from scans.rsi_scan import rsi_scan, format_rsi_message
from scans.new_high_scan import run_new_high_scan , format_new_high_message

load_dotenv()

TOKEN = os.getenv("TOKEN")

def send_to_telegram(recipient_id: str, message: str):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": recipient_id,
        "text": message
    }
    response = requests.post(url, data=payload)
    # ➕ 디버깅 로그 추가
    print(f"📤 텔레그램 전송 시도: chat_id={recipient_id}")
    print(f"📨 메시지 길이: {len(message)}")
    print(f"📨 메시지 미리보기: {message[:100]}")

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"❌ 텔레그램 전송 실패: {e}")
        print(f"🔍 응답 내용: {response.text}")
        raise e

    return response.json()


def background_search_and_notify(chat_id: str, code: str):
    if code == "1":
        df = rsi_scan()
        message = format_rsi_message(df)
    elif code == "2":
        df = long_lower_shadow_scan()
        message = format_shadow_message(df)
    elif code == '3' :
        df = run_new_high_scan()
        message = format_new_high_message(df)
    else:
        message = "❌ 지원하지 않는 코드입니다."

    send_to_telegram(chat_id, message)