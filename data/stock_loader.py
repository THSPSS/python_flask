import os

import pandas as pd
from functools import lru_cache
import requests
from io import StringIO
from datetime import datetime
from pathlib import Path

from utils.stock_utils import us_is_stock_today, us_is_valid_symbol, us_is_common_stock


# 공통 다운로드 및 포맷팅 함수
@lru_cache(maxsize=1)
def load_stock_data():
    """KRX 상장 종목의 코드와 회사명을 dict로 반환"""
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
    df = pd.read_html(url, encoding="euc-kr")[0]
    df = df[['종목코드', '회사명']].copy()
    return df

#종목 코드와 회사명
def get_stock_name_map():
    """종목코드 → 회사명 딕셔너리 반환"""
    df = load_stock_data()
    return dict(zip(df['종목코드'], df['회사명']))

# ✅ 이름 → 코드 매핑 딕셔너리
def get_code_dict_by_name() -> dict:
    df = load_stock_data()
    return dict(zip(df['회사명'], df['종목코드']))

#종목 코드 리스트화
def get_stock_universe():
    """종목코드 리스트 반환"""
    df = load_stock_data()
    return df['종목코드'].tolist()


### 📌 미국 주식 로딩 (캐시 기반)

# 📁 디렉토리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, 'raw')
CACHE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'cache'))
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# FTP URL
NASDAQ_URL = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/nasdaqlisted.txt"
OTHER_URL = "ftp://ftp.nasdaqtrader.com/SymbolDirectory/otherlisted.txt"

# 캐시 경로
CACHE_FILE = os.path.join(CACHE_DIR, "combined_stock_list.csv")

def get_us_cache_path():
    today_str = datetime.now().strftime("%Y%m%d")
    return CACHE_DIR / f"us_symbols_{today_str}.csv"


def get_us_stock_map():
    """하루 1회만 NASDAQ + NYSE + AMEX 보통주 리스트 캐싱 & 딕셔너리로 반환"""

    if us_is_stock_today(CACHE_FILE):
        print("📦 오늘자 캐시 존재: 캐시에서 로딩 중...")
        df = pd.read_csv(CACHE_FILE)
    else:
        print("🔄 캐시 없음 또는 오래됨: 원본 다운로드 및 재처리")

        # 파일 경로
        nasdaq_fallback = os.path.join(RAW_DIR, 'nasdaqlisted.txt')
        other_fallback = os.path.join(RAW_DIR, 'otherlisted.txt')

        # 📥 NASDAQ
        try:
            print("📥 NASDAQ 데이터 다운로드 중...")
            nasdaq_df = pd.read_csv(NASDAQ_URL, sep='|')
            nasdaq_df.to_csv(nasdaq_fallback, sep='|', index=False)
        except Exception as e:
            print("❌ NASDAQ 다운로드 실패 → 로컬 사용:", e)
            if os.path.exists(nasdaq_fallback):
                nasdaq_df = pd.read_csv(nasdaq_fallback, sep='|')
            else:
                raise FileNotFoundError("❌ nasdaqlisted.txt 없음")

        # 📥 OTHER
        try:
            print("📥 OTHER 데이터 다운로드 중...")
            other_df = pd.read_csv(OTHER_URL, sep='|')
            other_df.to_csv(other_fallback, sep='|', index=False)
        except Exception as e:
            print("❌ OTHER 다운로드 실패 → 로컬 사용:", e)
            if os.path.exists(other_fallback):
                other_df = pd.read_csv(other_fallback, sep='|')
            else:
                raise FileNotFoundError("❌ otherlisted.txt 없음")

        # ✅ 필터링 및 정제
        nasdaq_df = nasdaq_df[(nasdaq_df["Test Issue"] == "N") & (nasdaq_df["ETF"] == "N")]
        nasdaq_df = nasdaq_df[["Symbol", "Security Name"]].copy()

        other_df = other_df[(other_df["Test Issue"] == "N") & (other_df["ETF"] == "N")]
        other_df = other_df[["ACT Symbol", "Security Name"]].rename(columns={"ACT Symbol": "Symbol"})

        df = pd.concat([nasdaq_df, other_df], ignore_index=True)

        before_count = len(df)
        df = df[df["Symbol"].apply(us_is_valid_symbol)]
        df = df[df["Security Name"].apply(us_is_common_stock)]
        after_count = len(df)

        print(f"🧹 필터링 완료: {before_count} → {after_count} 종목")

        # 💾 캐시 저장
        df.to_csv(CACHE_FILE, index=False)
        print(f"💾 캐시 저장 완료: {CACHE_FILE}")

    # ✅ 2. 딕셔너리로 반환
    symbol_dict = {
        row["Symbol"]: row["Security Name"]
        for _, row in df.iterrows()
        if isinstance(row["Symbol"], str) and isinstance(row["Security Name"], str)
    }

    return symbol_dict

