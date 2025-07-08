from utils.stock_utils import is_valid_stock

# test_rsi.py
from scans.rsi_scan import rsi_scan
df = rsi_scan()
print(df)

# test_shadow.py
from scans.long_shadow_scan import long_lower_shadow_scan
df = long_lower_shadow_scan()
print(df)

# test_new_high.py
from scans.new_high_scan import new_high_scan
df = new_high_scan()
print(df)

from scans.new_high_scan import run_new_high_scan
df = run_new_high_scan()
df_clean = df[df["stk_nm"].apply(is_valid_stock)]
print(df_clean)