# scan/rsi_scan.py

import pandas as pd

from core.settings import RISE_THRESHOLD
from utils.filters import is_valid_candle_count, is_above_min_price
from utils.stock_utils import calc_rsi, get_korean_date_str
from scan.kr.kr_base_scanner import run_scan


def rsi_strategy(df, name, code):
    df["close"] = df["cur_prc"].astype(int)
    closes = df["close"].iloc[::-1].values

    if not is_valid_candle_count(closes):
        return None

    today_close = closes[-1]
    yesterday_close = closes[-2]
    past_range = closes[-23:-3]

    #기본 종가 가격 필터
    if not is_above_min_price(today_close):
        return None

    if yesterday_close >= min(past_range):
        return None

    rsi_yesterday = calc_rsi(closes[-16:-2])
    rsi_values = [calc_rsi(closes[i - 13:i + 1]) for i in range(len(closes) - 23, len(closes) - 3)]

    if rsi_yesterday <= min(rsi_values):
        return None

    rise_rate = (today_close - yesterday_close) / yesterday_close * 100
    if rise_rate < RISE_THRESHOLD:
        return None

    return {
        "종목코드": code,
        "종목명": name,
        "어제종가": yesterday_close,
        "오늘종가": today_close,
        "상승률%": round(rise_rate, 2),
        "어제RSI": rsi_yesterday,
        "최저RSI": min(rsi_values)
    }

def rsi_scan():
    return run_scan(rsi_strategy)


def format_rsi_message(df: pd.DataFrame) -> str:
    if df.empty:
        return "❗조건을 만족하는 종목이 없습니다."

    now_time_format = get_korean_date_str()

    message = f"📊 {now_time_format} RSI 20일 조건 종목 알림\n\n" + "\n\n".join([
        f"🔹 {row['종목명']} ({row['종목코드']})\n📈 상승률: {row['상승률%']}%\nRSI: {row['어제RSI']} > {row['최저RSI']}"
        for _, row in df.iterrows()
    ])
    return message