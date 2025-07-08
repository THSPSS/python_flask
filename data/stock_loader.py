import pandas as pd
from functools import lru_cache

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

#종목 코드 리스트화
def get_stock_universe():
    """종목코드 리스트 반환"""
    df = load_stock_data()
    return df['종목코드'].tolist()
