from utils.stock_utils import (
    get_token, get_stock_universe, get_stock_name_map
)

def load_market_data():
    token = get_token()
    codes = get_stock_universe()
    names = get_stock_name_map()
    return token, codes, names