from scans.base_scanner import run_scan
from utils.filters import is_above_min_price
from utils.stock_utils import fetch_daily_chart, is_valid_stock, is_52week_high
from datetime import datetime
import pandas as pd, time

def new_high_strategy(df, name, code):
    df = df.iloc[::-1]  # 날짜순 정렬
    closes = df["cur_prc"].astype(int).values

    if len(closes) < 250:
        return None

    today_close = closes[-1]
    past_250 = closes[-250:]

    if is_above_min_price(today_close):
        return None

    if not is_52week_high(past_250, today_close):
        return None

    print(name)

    return {
        "종목코드": code,
        "종목명": name,
        "오늘종가": today_close,
        "최고종가": max(past_250)
    }

def new_high_scan():
    return run_scan(new_high_strategy)


def format_new_high_message(df: pd.DataFrame) -> str:
    if df.empty:
        return "❗250일 신고가 종목이 없습니다."

    now = datetime.now()
    now_str = now.strftime("%y-%m-%d (%a)")

    return f"📈 {now_str} 기준 250일 신고가 종목\n\n" + "\n\n".join([
        f"🔹 {row['종목명']} ({row['종목코드']})\n📈 종가: {row['오늘종가']} / 신고가: {row['최고종가']}"
        for _, row in df.iterrows()
    ])