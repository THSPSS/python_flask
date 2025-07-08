import requests
from scans.base_scanner import run_scan
from utils.filters import is_above_min_price
from utils.stock_utils import is_valid_stock, is_52week_high , get_token
from datetime import datetime
import pandas as pd

#기존
def new_high_strategy(df, name, code):
    df = df.iloc[::-1]  # 날짜순 정렬
    closes = df["cur_prc"].astype(int).values

    if len(closes) < 250:
        return None

    today_close = closes[-1]
    past_250 = closes[-250:]

    if is_above_min_price(today_close):
        return None

    if not is_52week_high(past_250, today_close):
        return None

    print(name)

    return {
        "종목코드": code,
        "종목명": name,
        "오늘종가": today_close,
        "최고종가": max(past_250)
    }

#신규
def get_new_high_list(token: str) -> pd.DataFrame:
    """
    Kiwoom REST API를 이용해 신고가 종목 리스트 조회
    """
    url = "https://api.kiwoom.com/api/dostk/stkinfo"
    headers = {
        "authorization": f"Bearer {token}",
        "api-id": "ka10016"
    }
    payload = {
        "mrkt_tp": "000",              # 전체 시장
        "ntl_tp": "1",                 # 신고가
        "high_low_close_tp": "2",     # 고저 기준 1.고저기준 2.종가기준
        "stk_cnd": "0",                # 전체 조회
        "trde_qty_tp": "00000",
        "crd_cnd": "0",
        "updown_incls": "0",
        "dt": "250",
        "stex_tp": "1"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print("✅ 응답 수신 - 상태코드:", response.status_code)
        response.raise_for_status()
        data = response.json()

        return pd.DataFrame(data.get("ntl_pric", []))
    except Exception as e:
        print("❌ 52주 신고가 오류 발생:", e)
        return pd.DataFrame()

def run_new_high_scan():
    token = get_token()# 토큰만 발급
    df = get_new_high_list(token)

    if df.empty:
        print("❗신고가 종목이 없습니다.")
        return df

    print(f"✅ {len(df)}개의 신고가 종목 발견")
    return df

def filtering_stock(df):
    # 필터링
    df_filtered = df[df["stk_nm"].apply(is_valid_stock)]
    return df_filtered


def new_high_scan():
    return run_scan(new_high_strategy)

def format_new_high_message(df: pd.DataFrame) -> str:
    if df.empty:
        return "❗250일 신고가 종목이 없습니다."

    final_df =  filtering_stock(df)

    now = datetime.now()
    now_str = now.strftime("%y-%m-%d (%a)")

    return f"📈 {now_str} 기준 250일 신고가 종목\n\n" + "\n\n".join([
        f"🔹 {row['stk_nm']} ({row['stk_cd']})\n📈 현재가: {row['cur_prc']}"
        for _, row in  final_df.iterrows()
    ])