MIN_CANDLE_COUNT = 23
MIN_CLOSE_PRICE = 1000
US_MIN_CLOSE_PRICE = 1
MIN_VOLUME = 100000

def is_valid_candle_count(closes, min_count=MIN_CANDLE_COUNT):
    return len(closes) >= min_count

def is_above_min_price(close, threshold=MIN_CLOSE_PRICE):
    try:
        return int(close) >= threshold
    except ValueError:
        return False

#미국 1달러 이상 확인
def is_above_us_min_price(close, threshold=US_MIN_CLOSE_PRICE):
    try:
        return int(close) >= threshold
    except ValueError:
        return False

def is_above_min_volume(volume: int, threshold=MIN_VOLUME) -> bool:
    try:
        return int(volume) >= threshold
    except ValueError:
        return False