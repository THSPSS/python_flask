from scan.us.us_base_scanner import run_us_scan
from utils.filters import is_above_us_min_price, is_above_min_volume
from utils.stock_utils import get_korean_date_str


def us_new_high_strategy(df, symbol, name):
    closes = df["Close"].dropna().to_numpy()
    volumes = df["Volume"].dropna().to_numpy()

    if len(closes) < 250:
        return None

    today_close = closes[-1]
    today_volume = volumes[-1]
    past_250 = closes[-250:]

    if not is_above_us_min_price(today_close) or not is_above_min_volume(today_volume):
        return None

    print(f"✅ 신고가: {symbol} ({name})")

    return {
        "symbol": symbol,
        "name": name,
        "close": round(today_close, 2),
        "52w_high": round(max(past_250), 2)
    }


def format_us_52week_high(df):
    if df.empty:
        return "❗미국 52주 신고가 종목이 없습니다."

    now_time_format = get_korean_date_str()

    return f"📈 {now_time_format} 기준 미국 25주 신고가 종목\n\n" + "\n\n".join([
        f"🔹 {row['symbol']} ({row['name']})\n📈 52주 신고가: ${row['52w_high']}"
        for _, row in df.iterrows()
    ])

def us_new_high_scan():
    return run_us_scan(us_new_high_strategy)