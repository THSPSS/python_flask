# update_symbols.py
from data.stock_loader import get_us_stock_map, load_stock_data

if __name__ == "__main__":
    print("🔄 미국 종목 업데이트 중...")
    us_map = get_us_stock_map()
    print(f"✅ 미국 종목 {len(us_map)}개 저장 완료")

    print("🔄 한국 종목 업데이트 중...")
    kr_df = load_stock_data()
    print(f"✅ 한국 종목 {len(kr_df)}개 저장 완료")
