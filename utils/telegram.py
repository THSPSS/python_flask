import requests

from core.settings import MAX_LENGTH
from scan.kr.long_shadow_scan import long_lower_shadow_scan, format_shadow_message
from scan.kr.rsi_scan import rsi_scan, format_rsi_message
from scan.kr.new_high_scan import run_new_high_scan , format_new_high_message
from scan.us.long_lower_shadow import us_long_lower_shadow_scan, format_us_long_shadow
from scan.us.new_high_scan import us_new_high_scan, format_us_high
from scan.us.rsi_scan import us_rsi_scan, format_us_rsi_summary


# def send_to_telegram(recipient_id: str, message: str):
#     url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
#     payload = {
#         "chat_id": recipient_id,
#         "text": message
#     }
#     response = requests.post(url, data=payload)
#     # ➕ 디버깅 로그 추가
#     print(f"📤 텔레그램 전송 시도: chat_id={recipient_id}")
#     print(f"📨 메시지 길이: {len(message)}")
#     print(f"📨 메시지 미리보기: {message[:100]}")
#
#     try:
#         response.raise_for_status()
#     except requests.exceptions.HTTPError as e:
#         print(f"❌ 텔레그램 전송 실패: {e}")
#         print(f"🔍 응답 내용: {response.text}")
#         raise e
#
#     return response.json()


def send_file_to_telegram(token: str, recipient_id: str, file_path: str, caption: str = ""):
    print(f"📤 텔레그램 파일 전송 시도: chat_id={recipient_id}")
    print(f"📁 파일 경로: {file_path}")
    print(f"📝 캡션: {caption}")

    url = f"https://api.telegram.org/bot{token}/sendDocument"

    try:
        with open(file_path, "rb") as f:
            response = requests.post(
                url,
                data={"chat_id": recipient_id, "caption": caption},
                files={"document": f}
            )
        if response.status_code == 200:
            print(f"✅ 파일 전송 성공: {file_path}")
        else:
            print(f"❌ 파일 전송 실패: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")



def send_to_telegram(token: str,recipient_id: str, message: str = "", file_path : str = ""):
    print(f"📤 텔레그램 전송 시도: chat_id={recipient_id}")
    print(f"📤 토큰 확인: token={token}")
    print(f"📨 전체 메시지 길이: {len(message)}")
    print(f"📦 메시지 내용:\n{message}")  # ✅ 전체 메시지 출력

    # 파일 전송
    if file_path:
        send_file_to_telegram(token, recipient_id, file_path)

    # ✅ 4000자 이하일 경우 한 번에 전송
    if len(message) <= MAX_LENGTH:
        _send_chunk(token, recipient_id, message.strip())
        return

    lines = message.split('\n\n')  # 📌 문단 단위로 나눔
    chunk = ""

    for line in lines:
        if len(chunk) + len(line) + 2 <= MAX_LENGTH:
            chunk += line + "\n\n"
        else:
            _send_chunk(token, recipient_id, chunk.strip())
            chunk = line + "\n\n"

    if chunk:
        _send_chunk(token, recipient_id, chunk.strip())



def _send_chunk(token, recipient_id, text):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    print(f"전송 메시지 확인 : {text}")
    print(f"📨 전송 중... 길이: {len(text)}")
    payload = {
        "chat_id": recipient_id,
        "text": text
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"❌ 텔레그램 전송 실패: {e}")
        print(f"🔍 응답 내용: {response.text}")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

def background_search_and_notify(token: str ,chat_id: str, code: str):
    print(f"🛰️ 실행 요청: {code} → chat_id: {chat_id}")
    if code.startswith("us-"):
        us_code = code.replace("us-", "")
        if us_code == "rsi":
            df = us_rsi_scan()
            message = format_us_rsi_summary(df)
        elif us_code == "long-lower-shadow":
            df = us_long_lower_shadow_scan()
            message = format_us_long_shadow(df)
        elif us_code == "52weeks":
            df = us_new_high_scan()
            message = format_us_high(df)
        else:
            message = f"❌ 지원하지 않는 미국 코드입니다: {us_code}"
    else:
        if code == "rsi":
            df = rsi_scan()
            message = format_rsi_message(df)
        elif code == "long-lower-shadow":
            df = long_lower_shadow_scan()
            message = format_shadow_message(df)
        elif code == "52weeks":
            df = run_new_high_scan()
            message = format_new_high_message(df)
        else:
            message = f"❌ 지원하지 않는 한국 코드입니다: {code}"

    send_to_telegram(token , chat_id , message)