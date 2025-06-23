# scans/base_scanner.py

from utils.data_loader import load_market_data
from utils.stock_utils import is_valid_stock, fetch_daily_chart
from utils.filters import is_above_min_price
from datetime import datetime
import time
import pandas as pd

def run_scan(strategy_func):
    token, codes, names = load_market_data()
    today = datetime.now().strftime("%Y%m%d")
    print(f"today {today}")
    results = []

    for idx, code in enumerate(codes, 1):
        try:
            name = names.get(code, "")
            if not is_valid_stock(name):
                continue

            df = fetch_daily_chart(token, code, today)
            if df.empty:
                continue

            result = strategy_func(df, name, code)
            if result:
                results.append(result)

        except Exception as e:
            print(f"⚠️ {code} 분석 중 오류: {e}")
            time.sleep(0.2)

        if idx % 50 == 0:
            time.sleep(0.7)

    return pd.DataFrame(results)
