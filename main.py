"""
author : you
desc   : RSI 20-day bottom-breakout scanner (Kiwoom REST)
env    : Python 3.10+, requests, pandas, numpy
"""
import  time, requests, pandas as pd, numpy as np
from datetime import datetime, timedelta
from kiwoom_auth import get_token


# ───────────────────────── 유틸 함수 ────────────────────────────
def get_stock_name_map():
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
    df = pd.read_html(url, encoding="euc-kr")[0]
    df = df[['종목코드', '회사명']].copy()
    df.loc[:, '종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
    return dict(zip(df['종목코드'], df['회사명']))


def get_stock_universe() -> list[str]:
    """
    KOSPI + KOSDAQ 코드 긁어오기
    ▶ Kiwoom REST에 아직 전종목 리스트 API가 없으므로
      - (권장) KRX CSV (http://kind.krx.co.kr/filedownload/...) 를 주기적 다운로드
      - 또는 사전에 로컬 CSV 유지
    여기서는 간단히 CSV 링크 예시를 사용.
    """
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"  # KRX 상장법인목록
    df  = pd.read_html(url, encoding="euc-kr")[0]
    df = df.copy()  # avoid chained assignment warning
    df.loc[:, '종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
    return df["종목코드"].tolist()

def fetch_daily_chart(token:str, code:str, base_date:str):
    """
    ka10081  (일봉 차트)  한 번 호출 = 600개 캔들
    base_date 포함 과거순 정렬(최근->과거)
    """
    url = "https://api.kiwoom.com/api/dostk/chart"
    hdr = {
        "Content-Type": "application/json;charset=UTF-8",
        "authorization": f"Bearer {token}",
        "api-id": "ka10081",
        "cont-yn": "N",
        "next-key": ""
    }
    body = {
        "stk_cd": code,
        "base_dt": base_date,       # YYYYMMDD
        "upd_stkpc_tp": "1"         # 수정주가(1) 권장
    }
    r = requests.post(url, headers=hdr, json=body, timeout=10)
    r.raise_for_status()
    data = r.json()["stk_dt_pole_chart_qry"]
    return pd.DataFrame(data)

def calc_rsi(arr, period=14):
    deltas = np.diff(arr)
    gains  = np.where(deltas>0, deltas, 0)
    losses = np.where(deltas<0, -deltas,0)
    rs = (gains[:period].mean()) / (losses[:period].mean() or 1e-4)
    return round(100 - 100/(1+rs),2)


# ───────────────────────── 메인 스캐너 ───────────────────────────
EXCLUDE = ['ETN','KODEX','TIGER','KBSTAR','KOSEF','HANARO','ARIRANG',
           'FOCUS','스팩','SOL','RISE','BNK','우','1우','2우','3우',
           '우B','우C','우선주','KOACT']

def scan():
    token = get_token()
    codes  = get_stock_universe()
    today  = datetime.now().strftime("%Y%m%d")
    code_name_map = get_stock_name_map()

    results = []
    for idx, code in enumerate(codes,1):
        try:
            df = fetch_daily_chart(token, code, today)
            if len(df) < 22:                    # 데이터 부족
                continue

            #name = df.loc[0,"stk_infr"] if "stk_infr" in df else ""
            name = code_name_map.get(code, "")
            print(f"✅ {name}")
            if any(k in name.upper() for k in EXCLUDE):
                continue

            df["close"] = df["cur_prc"].astype(int)
            closes = df["close"].iloc[::-1].values  # 과거→현재

            today_close, y_close = closes[-1], closes[-2]

            past = closes[-22:-2]                # T-22 ~ T-3 (20개)
            if y_close >= past.min():            # (조건 2)
                continue

            low_idx = np.where(past == past.min())[0][0]
            abs_idx = len(closes)-22 + low_idx

            rsi_low = calc_rsi(closes[abs_idx-14:abs_idx])
            rsi_y   = calc_rsi(closes[-16:-2])

            if rsi_low >= rsi_y:                 # (조건 3)
                continue

            rise_rate = (today_close - y_close) / y_close *100
            if rise_rate < 3:                    # (조건 4)
                continue

            results.append({
                "종목코드": code,
                "종목명": name,
                "어제종가": y_close,
                "오늘종가": today_close,
                "상승률%":  round(rise_rate,2),
                "어제RSI":  rsi_y,
                "최저RSI":  rsi_low
            })
        except Exception as e:
            # API 호출제한 완화용 sleep & continue
            time.sleep(0.2)
            continue

        # 속도·요율 제한 완화
        if idx % 50 == 0:
            time.sleep(0.7)

    return pd.DataFrame(results)

if __name__ == "__main__":
    df = scan()
    print(df)