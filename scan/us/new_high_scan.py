from scan.us.us_base_scanner import run_us_scan
from utils.filters import is_above_us_min_price, is_above_min_volume
from utils.stock_utils import get_korean_date_str


def us_new_high_strategy(df, symbol, name , date : int = 250):
    closes = df["Close"].dropna().to_numpy()
    volumes = df["Volume"].dropna().to_numpy()

    if len(closes) < date:
        return None

    today_close = closes[-1]
    today_volume = volumes[-1]
    past_date = closes[-date:]
    max_close = max(past_date)

    if not is_above_us_min_price(today_close) or not is_above_min_volume(today_volume):
        return None

    if today_close < max_close:
        return None  # ✅ 오늘 종가가 신고가가 아니면 제외

    print(f"✅ 신고가: {symbol} ({name})")

    return {
        "symbol": symbol,
        "name": name,
        "close": round(today_close, 2),
        "w_high": round(max(past_date), 2)
    }


def format_us_high(df , date : str):
    if df.empty:
        return "❗미국 신고가 종목이 없습니다."

    now_time_format = get_korean_date_str()

    return f"📈 {now_time_format} 기준 미국 {date}주 신고가 종목\n\n" + "\n\n".join([
        f"🔹 {row['symbol']} ({row['name']})\n 📈 ${row['w_high']}"
        for _, row in df.iterrows()
    ])

def us_new_high_scan(date: int = 250):
    return run_us_scan(lambda df, symbol, name: us_new_high_strategy(df, symbol, name, date=date))