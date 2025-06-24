import pandas as pd, numpy as np
from dotenv import load_dotenv
import requests
import os


load_dotenv()

APP_KEY    = os.getenv("KIWOOM_APP_KEY")
SECRET_KEY = os.getenv("KIWOOM_SECRET_KEY")

EXCLUDE_KEYWORDS = [
    'ETN','KODEX','TIGER','KBSTAR','KOSEF','HANARO','ARIRANG',
    'FOCUS','스팩','SOL','RISE','BNK','우','1우','2우','3우',
    '우B','우C','우선주','KOACT',"KIWOOM","지주","ACE", "PLUS","50","200"
]

RSI_PERIOD = 14 #RSI 검색을 위한 일수
MIN_CANDLE_COUNT = 23 #최소 종가 count
RISE_THRESHOLD = 3  # 어제 대비 오늘 증가 %


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

#종목 코드와 회사명
def get_stock_name_map():
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
    df = pd.read_html(url, encoding="euc-kr")[0]
    df = df[['종목코드', '회사명']].copy()
    df['종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
    return dict(zip(df['종목코드'], df['회사명']))

#종목 코드 리스트화
def get_stock_universe():
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
    df = pd.read_html(url, encoding="euc-kr")[0]
    df['종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
    return df['종목코드'].tolist()


#리츠, ETF , ETN 등등 빼기
def is_valid_stock(name):
    return not any(keyword in name.upper() for keyword in EXCLUDE_KEYWORDS)


#일봉 차트 데이터 가져오기
def fetch_daily_chart(token, code, base_date):
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
    r = requests.post(url, headers=headers, json=body, timeout=10)
    r.raise_for_status()
    data = r.json().get("stk_dt_pole_chart_qry", [])
    return pd.DataFrame(data)

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
