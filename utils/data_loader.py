from utils.stock_utils import get_token
from data.stock_loader import load_stock_data

def load_market_data():
    token = get_token()
    df = load_stock_data()  # 이미 format_code 적용됨
    code_name_map = dict(zip(df['종목코드'], df['회사명']))

    # 필요한 로직으로 codes만 추출 (예: KOSPI, 코스닥 필터링 등 추가 가능)
    codes = df['종목코드'].tolist()
    return token, codes, code_name_map