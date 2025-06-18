import time, requests, pandas as pd, numpy as np
from datetime import datetime
from kiwoom_auth import get_token

# ────────────────────── 상수 정의 ──────────────────────
EXCLUDE_KEYWORDS = [
    'ETN','KODEX','TIGER','KBSTAR','KOSEF','HANARO','ARIRANG',
    'FOCUS','스팩','SOL','RISE','BNK','우','1우','2우','3우',
    '우B','우C','우선주','KOACT'
]
RSI_PERIOD = 14 #RSI 검색을 위한 일수
MIN_CANDLE_COUNT = 23 #최소 종가 count
RISE_THRESHOLD = 3  # 어제 대비 오늘 증가 %


# ────────────────────── 유틸 함수 ──────────────────────
def get_stock_name_map():
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
    df = pd.read_html(url, encoding="euc-kr")[0]
    df = df[['종목코드', '회사명']].copy()
    df['종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
    return dict(zip(df['종목코드'], df['회사명']))

def get_stock_universe():
    url = "https://kind.krx.co.kr/corpgeneral/corpList.do?method=download"
    df = pd.read_html(url, encoding="euc-kr")[0]
    df['종목코드'] = df['종목코드'].apply(lambda x: f"{x:06d}")
    return df['종목코드'].tolist()

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

def calc_rsi(prices, period=RSI_PERIOD):
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean() or 1e-4
    rs = avg_gain / avg_loss
    return round(100 - 100 / (1 + rs), 2)

def is_valid_stock(name):
    return not any(keyword in name.upper() for keyword in EXCLUDE_KEYWORDS)


# ────────────────────── 분석 로직 ──────────────────────
def analyze_stock(df, name, code):
    df["close"] = df["cur_prc"].astype(int)
    closes = df["close"].iloc[::-1].values  # 과거 → 현재

    #필터 1 : 최소 일수 확인(예시 : 23일)
    if len(closes) < MIN_CANDLE_COUNT:
        return None

    today_close = closes[-1]
    yesterday_close = closes[-2]
    past_range = closes[-23:-3]

    #필터 2 : 현재가가 1000원 미만
    if today_close < 1000:
        return None

    # 조건 1: 어제 종가가 과거 20일 최저가보다 낮아야
    if yesterday_close >= min(past_range):
        return None

    # 조건 2: 어제 RSI
    rsi_yesterday = calc_rsi(closes[-16:-2])

    # 조건 2: 과거 RSI 리스트 생성
    rsi_values = []
    for i in range(len(closes) - 23, len(closes) - 3):
        if i < RSI_PERIOD - 1:
            continue
        segment = closes[i - (RSI_PERIOD - 1):i + 1]
        rsi = calc_rsi(segment)
        rsi_values.append(rsi)

    # 조건 2: 어제 RSI 값이 과거 20일 RSI 값 중 최저값 이상
    if rsi_yesterday <= min(rsi_values):
        print(f"{name} ❌ 어제 RSI {rsi_yesterday} <= 과거 최저 RSI {min(rsi_values)}")
        return None
    else:
        print(f"{name} ✅ 어제 RSI {rsi_yesterday} > 과거 최저 RSI {min(rsi_values)}")

    # 조건 3: 상승률 3% 이상
    rise_rate = (today_close - yesterday_close) / yesterday_close * 100
    if rise_rate < RISE_THRESHOLD:
        return None

    return {
        "종목코드": code,
        "종목명": name,
        "어제종가": yesterday_close,
        "오늘종가": today_close,
        "상승률%": round(rise_rate, 2),
        "어제RSI": rsi_yesterday,
        "최저RSI": min(rsi_values)
    }


# ────────────────────── 메인 스캐너 ──────────────────────
def scan():
    #api request를 위한 token 값
    token = get_token()
    codes = get_stock_universe()
    names = get_stock_name_map()
    today = datetime.now().strftime("%Y%m%d")

    results = []
    for idx, code in enumerate(codes, 1):
        try:
            name = names.get(code, "")
            if not is_valid_stock(name):
                continue

            df = fetch_daily_chart(token, code, today)
            if df.empty:
                continue

            result = analyze_stock(df, name, code)
            if result:
                results.append(result)

        except Exception as e:
            print(f"⚠️ {code} 분석 중 오류: {e}")
            time.sleep(0.2)
            continue

        if idx % 50 == 0:
            time.sleep(0.7)

    return pd.DataFrame(results)


# ────────────────────── 실행 ──────────────────────
if __name__ == "__main__":
    df = scan()
    print(df)