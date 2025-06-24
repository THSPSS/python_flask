# scans/long_shadow_scan.py
import pandas as pd
from scans.base_scanner import run_scan
from utils.filters import is_above_min_price, is_above_min_volume
from datetime import datetime

def long_shadow_strategy(df, name, code):
    df = df.iloc[::-1]  # 날짜 정렬
    today = df.iloc[-1]

    open_p = int(today['open_pric'])
    close_p = int(today['cur_prc'])
    low = int(today['low_pric'])
    volume = int(today['trde_qty'])

    print(name)

    #필터 1000원 이하
    if not is_above_min_price(close_p):
        return None

    #필터 거래량 10000이하
    if not is_above_min_volume(volume):
        return None

    body = abs(open_p - close_p)
    lower_shadow = min(open_p, close_p) - low
    body_ratio = body / open_p
    shadow_ratio = lower_shadow / low

    if body == 0 or shadow_ratio < 0.05 < body_ratio or lower_shadow < body * 3:
        return None

    return {
        "종목코드": code,
        "종목명": name,
        "시가": open_p,
        "종가": close_p,
        "저가": low,
        "거래량": volume,
        "아래꼬리비율": shadow_ratio
    }

def long_lower_shadow_scan():
    return run_scan(long_shadow_strategy)


def format_shadow_message(df: pd.DataFrame) -> str:
    if df.empty:
        return "❗아래꼬리 조건을 만족하는 종목이 없습니다."

    now = datetime.now()
    now_time_format = now.strftime("%y-%m-%d") + f"({['월','화','수','목','금','토','일'][now.weekday()]})"

    message = f"📊 {now_time_format} 아래꼬리 종목 알림\n\n".join([
        f"🔹 {row['종목명']} ({row['종목코드']})\n💧 종가: {row['종가']}원\n꼬리비율: {round(row['아래꼬리비율']*100, 2)}%"
        for _, row in df.iterrows()
    ])
    return message
