# handlers/dispatcher.py
from scans.rsi_scan import rsi_scan
from scans.long_shadow_scan import long_lower_shadow_scan

search_map = {
    "1": rsi_scan,
    "2": long_lower_shadow_scan
}

def handle_search(code: str):
    search_func = search_map.get(code)
    if not search_func:
        raise ValueError("지원하지 않는 코드입니다.")
    return search_func()
