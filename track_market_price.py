import os
import time

import pandas as pd
from datetime import datetime  # 인증 토큰 발급 함수

from data.stock_loader import get_code_dict_by_name
from utils.stock_utils import fetch_daily_chart, get_token


def build_name_code_map(base_file_path: str) -> dict:
    df_base = pd.read_excel(base_file_path)

    if "종목명" not in df_base.columns:
        raise ValueError("❌ '종목명' 컬럼이 필요합니다.")

    name_list = df_base["종목명"].dropna().tolist()
    code_dict = get_code_dict_by_name()  # {회사명: 종목코드}

    name_code_map = {}
    unmatched = []

    # ✅ 수동 예외 매핑 추가
    manual_code_map = {
        "sk바이오팜": "326030"
    }

    for name in name_list:
        matched_code = None

        # 0. 수동 매핑 우선 (대소문자 무시)
        lowered_name = name.lower()
        if lowered_name in manual_code_map:
            matched_code = manual_code_map[lowered_name]

        # 1. 완전 일치
        elif name in code_dict:
            matched_code = code_dict[name]

        # 2. 부분 일치 (예: '삼성화재' in '삼성화재해상보험')
        else:
            for full_name, code in code_dict.items():
                if name in full_name:
                    matched_code = code
                    break

        if matched_code:
            name_code_map[name] = matched_code
        else:
            unmatched.append(name)

    if unmatched:
        print(f"❗매칭 실패 종목: {unmatched}")

    return name_code_map

def get_today_closes(token: str, name_code_map: dict) -> dict:
    today = datetime.today().strftime("%Y%m%d")
    closes = {}

    for name, code in name_code_map.items():
        print(name , code)
        df = fetch_daily_chart(token, code, base_date=today)
        if df.empty:
            continue

        try:
            close_price = int(float(df.iloc[0]["cur_prc"] or 0))
            closes[name] = close_price
            time.sleep(0.2)  # 또는 random.uniform(0.2, 0.6)
        except Exception as e:
            print(f"⚠️ {name} 종가 추출 실패: {e}")

    return closes


def update_price_history_from_kiwoom(base_file_path: str):
    """코스피 100.xlsx 기준으로 종가 기록 누적 저장"""
    today_col = datetime.today().strftime("%Y-%m-%d")

    df_base = pd.read_excel(base_file_path)
    if "종목명" not in df_base.columns:
        raise ValueError("❌ '종목명' 컬럼이 필요합니다.")

    # ✅ symbol dict → {symbol: name} → name to code 역맵핑
    name_list = df_base["종목명"].dropna().tolist()
    name_code_map = build_name_code_map(base_file_path)

    token = get_token()
    price_map = get_today_closes(token, name_code_map)

    # ✅ 히스토리 파일 업데이트
    history_file = base_file_path.replace(".xlsx", "_history.xlsx")
    if os.path.exists(history_file):
        df_history = pd.read_excel(history_file, index_col=0)
    else:
        # 🆕 히스토리 파일 처음 생성 시: 종목명 + 종목코드로 시작
        df_history = pd.DataFrame({
            "종목코드": pd.Series(name_code_map)
        })
        df_history.index.name = "종목명"

    df_history[today_col] = pd.Series(price_map)
    df_history = df_history.sort_index()
    df_history.to_excel(history_file)
    print(f"✅ 저장 완료: {history_file}")

if __name__ == "__main__":
    update_price_history_from_kiwoom("data/tracking/코스닥 시가총액 100 20250711T1044.xlsx")
    update_price_history_from_kiwoom("data/tracking/코스피 시가총액 100 20250711T1044.xlsx")