from scan.us.us_base_scanner import run_us_scan
from utils.filters import is_above_us_min_price, is_above_min_volume
from utils.stock_utils import get_korean_date_str


def long_shadow_strategy(df, symbol, name):
    if len(df) < 2:
        return None

    row = df.iloc[-1]
    open_price = row['Open']
    close_price = row['Close']
    low_price = row['Low']
    volume = row['Volume']

    print(f"🔍 {symbol} 시가: {open_price}, 종가: {close_price}, 저가: {low_price}, 거래량: {volume}")

    if not is_above_us_min_price(close_price) or not is_above_min_volume(volume):
        return None

    body = abs(close_price - open_price)
    lower_shadow = min(open_price, close_price) - low_price
    body_ratio = body / open_price if open_price else 0
    shadow_ratio = lower_shadow / low_price if low_price else 0

    if (
        body > 0 and
        shadow_ratio > 0.05 > body_ratio and
        lower_shadow > body * 3
    ):
        return {
            "symbol": symbol,
            "name": name,
            "close": round(close_price, 2),
            "lower_shadow_ratio": shadow_ratio
        }

    return None


def format_us_long_shadow(df):
    if df.empty:
        return "❗아래꼬리 조건을 만족하는 미국 종목이 없습니다."

    now_time_format = get_korean_date_str()

    message = f"📊 {now_time_format} 미국 아래꼬리 종목 알림\n\n"
    message += "\n\n".join([
        f"🔹 {row['symbol']} ({row['name']})\n"
        f"💧 종가: ${row['close']}\n"
        f"📏 꼬리비율: {round(row['lower_shadow_ratio'] * 100, 2)}%"
        for _, row in df.iterrows()
    ])
    return message

def us_long_lower_shadow_scan():
    return run_us_scan(long_shadow_strategy)