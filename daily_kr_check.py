import os
from dotenv import load_dotenv

from scan.kr.long_shadow_scan import long_lower_shadow_scan, format_shadow_message
from scan.kr.new_high_scan import run_new_high_scan, format_new_high_message
from utils.telegram import send_to_telegram

# 환경 변수 로드
load_dotenv()
BOT_TOKEN = os.getenv('TOKEN')
GROUP_ID = os.getenv('GROUP_ID')

# --- 검색기 함수 임포트 ---

def sequential_stock_checks():

    # 3. 💧 아래꼬리 검색
    print("▶️ 아래꼬리 검색 시작")
    df_shadow = long_lower_shadow_scan()
    msg_shadow = format_shadow_message(df_shadow)
    print(df_shadow)
    send_to_telegram(BOT_TOKEN, GROUP_ID, msg_shadow)


    # 1. 📊 30주 신고가
    print("▶️ 30주 신고가 검색 시작")
    df_30w = run_new_high_scan(date="150")
    msg_30w = format_new_high_message(df_30w, date="30")
    print(df_30w)
    send_to_telegram(BOT_TOKEN, GROUP_ID, msg_30w)

    # 2. 📊 52주 신고가
    print("▶️ 52주 신고가 검색 시작")
    df_52w = run_new_high_scan(date="250")
    msg_52w = format_new_high_message(df_52w, date="52")
    print(df_52w)
    send_to_telegram(BOT_TOKEN, GROUP_ID, msg_52w)



# 실행
if __name__ == "__main__":
    sequential_stock_checks()