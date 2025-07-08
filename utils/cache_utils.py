from datetime import date
from data.stock_loader import load_stock_data  # 또는 상대경로로 import

_last_cache_day = None

def refresh_cache_if_needed():
    global _last_cache_day
    today = date.today()
    if _last_cache_day != today:
        print("🔄 [캐시 초기화] load_stock_data()")
        load_stock_data.cache_clear()
        _last_cache_day = today