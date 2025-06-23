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