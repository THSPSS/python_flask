import numpy as np

from core.settings import RISE_THRESHOLD
from scan.us.us_base_scanner import run_us_scan
from utils.stock_utils import calc_rsi, get_korean_date_str


def us_rsi_strategy(df, symbol, name):
    if df.empty or len(df) < 60:
        return None

    df = df.dropna()
    closes = df['Close'].to_numpy()
    today_close = float(closes[-1])
    yesterday_close = float(closes[-2])

    past_range = closes[-62:-2]
    min_past = float(min(past_range))

    if yesterday_close >= min_past:
        return None

    lowest_idx = np.where(past_range == min_past)[0][0]
    absolute_idx = len(closes) - 62 + lowest_idx

    rsi_yesterday_seg = closes[-16:-2]
    rsi_lowest_seg = closes[absolute_idx - 14:absolute_idx]

    if len(rsi_yesterday_seg) < 14 or len(rsi_lowest_seg) < 14:
        return None

    rsi_yesterday = calc_rsi(np.array(rsi_yesterday_seg))
    rsi_lowest = calc_rsi(np.array(rsi_lowest_seg))

    if rsi_yesterday <= rsi_lowest:
        return None

    rise_rate = (today_close - yesterday_close) / yesterday_close * 100
    if rise_rate < RISE_THRESHOLD:
        return None

    return {
        'symbol': symbol,
        'name': name,
        'yesterday_close': round(yesterday_close, 2),
        'lowest_close': round(min_past, 2),
        'rsi_yesterday': rsi_yesterday,
        'rsi_lowest': rsi_lowest
    }


def format_us_rsi_summary(df):
    if df.empty:
        return "❗RSI 조건을 만족하는 미국 종목이 없습니다."

    now_time_format = get_korean_date_str()

    message = f"📊 {now_time_format} 미국 RSI 60일 조건 종목\n\n"

    for _, row in df.iterrows():
        message += (
            f"🔹 {row['symbol']} ({row['name']})\n"
            f"💵 어제 종가: ${row['yesterday_close']}\n"
            f"📉 60일중 최저가: ${row['lowest_close']}\n"
            f"📈 RSI: {row['rsi_yesterday']} > {row['rsi_lowest']}\n\n"
        )

    return message.strip()

def us_rsi_scan():
    return run_us_scan(us_rsi_strategy)