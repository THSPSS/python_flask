import time
from datetime import datetime

import pandas as pd, numpy as np
from dotenv import load_dotenv
import requests
import os

from core.settings import *

load_dotenv()

APP_KEY    = os.getenv("KIWOOM_APP_KEY")
SECRET_KEY = os.getenv("KIWOOM_SECRET_KEY")

# 미국-필터 조건
EXCLUDE_SUFFIXES = {'W', 'R', 'P', 'Q'}

#토큰 가져오기
def get_token() -> str:
    url = "https://api.kiwoom.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": SECRET_KEY
    }
    r = requests.post(url, json=payload, timeout=10)
    print("🔍 토큰 응답 내용:", r.status_code, r.text)  # 이 줄 추가
    r.raise_for_status()
    return r.json()["token"]


#리츠, ETF , ETN 등등 빼기
def is_valid_stock(name):
    return not any(keyword in name.upper() for keyword in EXCLUDE_KEYWORDS)


#일봉 차트 데이터 가져오기

def fetch_daily_chart(token, code, base_date, retries=5, delay=0.5):
    url = "https://api.kiwoom.com/api/dostk/chart"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "api-id": "ka10081",
        "cont-yn": "N",
        "next-key": ""
    }
    body = {
        "stk_cd": code,
        "base_dt": base_date,
        "upd_stkpc_tp": "1"
    }

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(url, headers=headers, json=body, timeout=10)
            if response.status_code == 429:
                wait_time = delay * attempt
                print(f"⏳ 요청 제한 (429) - {code} → {wait_time:.1f}s 후 재시도 ({attempt}/{retries})")
                time.sleep(wait_time)
                continue

            elif response.status_code >= 500:
                wait_time = delay * attempt + 1.0
                print(f"⛔ 서버 오류 ({response.status_code}) - {code} → {wait_time:.1f}s 후 재시도 ({attempt}/{retries})")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json().get("stk_dt_pole_chart_qry", [])
            if not data:
                print(f"⚠️ {code} 데이터 없음 또는 응답 비어 있음")
                return pd.DataFrame()

            return pd.DataFrame(data)

        except requests.exceptions.RequestException as e:
            wait_time = delay * attempt
            print(f"⚠️ 요청 실패 ({code}) → {e} → {wait_time:.1f}s 후 재시도")
            time.sleep(wait_time)

    print(f"❌ {code} 최종 요청 실패 (재시도 {retries}회)")
    return pd.DataFrame()

#RSI 계산
def calc_rsi(prices, period=RSI_PERIOD):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean() or 1e-4
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)


#52주 신고가 확인
def is_52week_high(closes: list[int], today_close: int) -> bool:
    return today_close >= max(closes)

#연도 - 월 - 일 (요일)
def get_korean_date_str():
    now = datetime.now()
    return now.strftime("%y-%m-%d") + f" ({WEEKDAY_MAP[now.weekday()]})"

def us_is_stock_today(file_path):
    """파일이 오늘 수정된 파일인지 확인"""
    if not os.path.exists(file_path):
        return False
    return datetime.fromtimestamp(os.path.getmtime(file_path)).date() == datetime.today().date()

def us_is_valid_symbol(symbol):
    return isinstance(symbol, str) and not (len(symbol) > 4 and symbol[-1].upper() in EXCLUDE_SUFFIXES)

def us_is_common_stock(name):
    return isinstance(name, str) and name.strip().endswith("- Common Stock")