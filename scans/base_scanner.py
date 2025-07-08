# scans/base_scanner.py
from concurrent.futures import ThreadPoolExecutor , as_completed

from utils.data_loader import load_market_data
from utils.stock_utils import is_valid_stock, fetch_daily_chart
from datetime import datetime
import pandas as pd

def run_scan(strategy_func):
    token, codes, name_map = load_market_data()
    today = datetime.now().strftime("%Y%m%d")
    results = []


    def process_code(code):
        try:
            name = name_map.get(code, "")
            if not is_valid_stock(name):
                return None

            df = fetch_daily_chart(token, code, today)
            if df.empty:
                return None

            result = strategy_func(df, name, code)
            return result
        except Exception as e:
            print(f"⚠️ {code} 분석 중 오류: {e}")
            return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_code, code) for code in codes]

        for idx, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result:
                results.append(result)

    return pd.DataFrame(results)