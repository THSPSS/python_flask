# scan/kr_base_scanner.py
import time
from concurrent.futures import ThreadPoolExecutor , as_completed

from utils.data_loader import load_market_data
from utils.stock_utils import is_valid_stock, fetch_daily_chart
from datetime import datetime
import pandas as pd

def run_scan(strategy_func):
    token, codes, name_map = load_market_data()
    today = datetime.now().strftime("%Y%m%d")
    results = []
    failed_codes = []

    start_time = time.time()

    for idx, code in enumerate(codes, 1):
        try:
            name = name_map.get(code, "")
            if not is_valid_stock(name):
                continue

            df = fetch_daily_chart(token, code, today)
            if df.empty:
                failed_codes.append((code, name))
                continue

            result = strategy_func(df, name, code)
            if result:
                results.append(result)

        except Exception as e:
            print(f"⚠️ {code} 분석 중 오류: {e}")
            failed_codes.append((code, name))

        time.sleep(0.6)  # ✅ API 요청 간 딜레이 (중요!)

    elapsed = time.time() - start_time
    print(f"\n🔚 전체 검색 완료! ⏱️ 소요 시간: {elapsed:.2f}초")

    # 로그
    if failed_codes:
        print("\n🚨 최종 실패 종목:")
        for code, name in failed_codes:
            print(f"❌ {code} {name}")

    return pd.DataFrame(results)