import os
from dotenv import load_dotenv

from scan.kr.long_shadow_scan import long_lower_shadow_scan, format_shadow_message
from scan.kr.new_high_scan import run_new_high_scan, format_new_high_message
from scan.us.long_lower_shadow import us_long_lower_shadow_scan, format_us_long_shadow
from scan.us.new_high_scan import us_new_high_scan, format_us_high
from utils.telegram import send_to_telegram

# 환경 변수 로드
load_dotenv()
BOT_TOKEN = os.getenv('TOKEN')
GROUP_ID = os.getenv('GROUP_ID')

# --- 검색기 함수 임포트 ---

def sequential_us_stock_checks():
    # 1. 📊 30주 신고가
    print("▶️ 미국 30주 신고가 검색 시작")
    df_30w = us_new_high_scan(date=150)
    msg_30w = format_us_high(df_30w, date="30")
    print(df_30w)
    send_to_telegram(BOT_TOKEN, GROUP_ID, msg_30w)

    # 2. 📊 52주 신고가
    print("▶️ 미국 52주 신고가 검색 시작")
    df_52w = us_new_high_scan(date=250)
    msg_52w = format_us_high(df_30w, date="52")
    print(df_52w)
    send_to_telegram(BOT_TOKEN, GROUP_ID, msg_52w)

    # 3. 💧 아래꼬리 검색
    print("▶️ 미국 아래꼬리 검색 시작")
    df_shadow = us_long_lower_shadow_scan()
    msg_shadow = format_us_long_shadow(df_shadow)
    print(df_shadow)
    send_to_telegram(BOT_TOKEN, GROUP_ID, msg_shadow)

# 실행
if __name__ == "__main__":
    sequential_us_stock_checks()