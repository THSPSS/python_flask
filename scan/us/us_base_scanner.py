import time
import pandas as pd
from yfinance import Ticker

from data.stock_loader import get_us_stock_map


def run_us_scan(strategy_func, limit=None):
    symbol_dict = get_us_stock_map() # {symbol: name}
    symbols = list(symbol_dict.keys())

    if limit:
        symbols = symbols[:limit]

    results = []
    failed = []

    print(f"🚀 미국 종목 {len(symbols)}개 검색 시작...")
    start_time = time.time()

    for idx, symbol in enumerate(symbols, 1):
        name = symbol_dict[symbol]
        label = f"{symbol} ({name})"

        try:
            print(f"🔍 [{idx:04}/{len(symbols)}] 분석 중: {label}")

            data = Ticker(symbol).history(period="1y")

            if data.empty or len(data) < 200:
                print(f"⚠️ {label}: 데이터 부족 또는 없음")
                continue

            # 👉 name을 strategy_func에 넘기고 결과에 포함
            result = strategy_func(data, symbol, name)
            if result:
                results.append(result)
                print(f"✅ 완료: {label}")

        except Exception as e:
            print(f"❌ 오류 - {label}: {e}")
            failed.append(symbol)

        time.sleep(0.1)

    elapsed = time.time() - start_time
    print(f"\n🔚 미국 주식 검색 완료! ⏱️ 소요 시간: {elapsed:.2f}초")

    if failed:
        print(f"\n🚨 실패 종목({len(failed)}):")
        for s in failed:
            print(f"❌ {s} ({symbol_dict.get(s, 'Unknown')})")

    return pd.DataFrame(results)
