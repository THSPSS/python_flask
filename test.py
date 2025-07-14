# test_rsi.py
# from scan.kr.rsi_scan import rsi_scan
# from utils.stock_utils import is_valid_stock
#
# df = rsi_scan()
# print(df)
#
# # test_shadow.py
# from scan.kr.long_shadow_scan import long_lower_shadow_scan
# df = long_lower_shadow_scan()
# print(df)
#
# # test_new_high.py
# from scan.kr.new_high_scan import new_high_scan
# df = new_high_scan()
# print(df)
#
# from scan.kr.new_high_scan import run_new_high_scan
# df = run_new_high_scan()
# df_clean = df[df["stk_nm"].apply(is_valid_stock)]
# print(df_clean)

# from scan.us.new_high_scan import us_new_high_scan
# df = us_new_high_scan()
# print(df)

# import pandas as pd
# from yahoo_fin import stock_info as si
#
# # gather stock symbols from major US exchanges
# df1 = pd.DataFrame( si.tickers_sp500() )
# df2 = pd.DataFrame( si.tickers_nasdaq() )
# df3 = pd.DataFrame( si.tickers_dow() )
# df4 = pd.DataFrame( si.tickers_other() )
#
# # convert DataFrame to list, then to sets
# sym1 = set( symbol for symbol in df1[0].values.tolist() )
# sym2 = set( symbol for symbol in df2[0].values.tolist() )
# sym3 = set( symbol for symbol in df3[0].values.tolist() )
# sym4 = set( symbol for symbol in df4[0].values.tolist() )
#
# # join the 4 sets into one. Because it's a set, there will be no duplicate symbols
# symbols = set.union( sym1, sym2, sym3, sym4 )
#
# # Some stocks are 5 characters. Those stocks with the suffixes listed below are not of interest.
# my_list = ['W', 'R', 'P', 'Q']
# del_set = set()
# sav_set = set()
#
# for symbol in symbols:
#     if len( symbol ) > 4 and symbol[-1] in my_list:
#         del_set.add( symbol )
#     else:
#         print(f"saved symbol: {symbol}")
#         sav_set.add( symbol )
#
# print( f'Removed {len( del_set )} unqualified stock symbols...' )
# print( f'There are {len( sav_set )} qualified stock symbols...' )

import os
import pandas as pd
from datetime import datetime

def is_today(file_path):
    """캐시 파일이 오늘 생성/수정된 것인지 확인"""
    if not os.path.exists(file_path):
        return False
    last_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
    return last_modified.date() == datetime.today().date()

# 📁 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'raw')
CACHE_DIR = os.path.join(BASE_DIR, '../../cache')


# 원본 파일 경로
nasdaq_fallback = os.path.join(RAW_DIR, 'nasdaqlisted.txt')
other_fallback = os.path.join(RAW_DIR, 'otherlisted.txt')
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)



# FTP 경로
nasdaq_url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt"
other_url = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt"

cache_file = os.path.join(CACHE_DIR, "combined_stock_list.csv")

if is_today(cache_file):
    print("📦 오늘 캐시 파일이 존재합니다. 다시 다운로드하지 않습니다.")
    combined_df = pd.read_csv(cache_file)
else:
    print("🔄 캐시 파일이 없거나 오래되었습니다. 새로 생성합니다.")

    # 📥 데이터 로딩
    try:
        print("📥 NASDAQ 데이터 로딩 중...")
        nasdaq_df = pd.read_csv(nasdaq_url, sep='|')
        nasdaq_df.to_csv(nasdaq_fallback, sep='|', index=False)
    except Exception as e:
        print("❌ NASDAQ FTP 접근 실패, 로컬 파일로 대체:", e)
        if os.path.exists(nasdaq_fallback):
            nasdaq_df = pd.read_csv(nasdaq_fallback, sep='|')
        else:
            raise FileNotFoundError("nasdaqlisted.txt 없음")

    try:
        print("📥 OTHER (NYSE/AMEX) 데이터 로딩 중...")
        other_df = pd.read_csv(other_url, sep='|')
        other_df.to_csv(other_fallback, sep='|', index=False)
    except Exception as e:
        print("❌ OTHER FTP 접근 실패, 로컬 파일로 대체:", e)
        if os.path.exists(other_fallback):
            other_df = pd.read_csv(other_fallback, sep='|')
        else:
            raise FileNotFoundError("otherlisted.txt 없음")

    # ✅ 정제
    nasdaq_df = nasdaq_df[(nasdaq_df["Test Issue"] == "N") & (nasdaq_df["ETF"] == "N")]
    nasdaq_df = nasdaq_df[["Symbol", "Security Name"]].copy()

    other_df = other_df[(other_df["Test Issue"] == "N") & (other_df["ETF"] == "N")]
    other_df = other_df[["ACT Symbol", "Security Name"]].rename(columns={"ACT Symbol": "Symbol"})

    combined_df = pd.concat([nasdaq_df, other_df], ignore_index=True)

    # ❌ 필터링
    exclude_suffixes = {'W', 'R', 'P', 'Q'}
    def is_valid_symbol(symbol):
        return isinstance(symbol, str) and not (len(symbol) > 4 and symbol[-1].upper() in exclude_suffixes)

    def is_common_stock(name):
        return isinstance(name, str) and name.strip().endswith("- Common Stock")

    before_count = len(combined_df)
    combined_df = combined_df[combined_df["Symbol"].apply(is_valid_symbol)]
    combined_df = combined_df[combined_df["Security Name"].apply(is_common_stock)]
    after_count = len(combined_df)

    print(f"🧹 필터링 완료: {before_count} → {after_count} 종목")

    # ✅ 캐시 저장
    cache_file = os.path.join(CACHE_DIR, "combined_stock_list.csv")
    combined_df.to_csv(cache_file, index=False)
    print(f"💾 캐시 저장 완료: {cache_file}")

    # ✅ 샘플
    print("\n📊 샘플:")
    print(combined_df.head(10))

