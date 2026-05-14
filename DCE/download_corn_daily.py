"""Download DCE corn main-contract daily data via AKShare."""
from pathlib import Path
import akshare as ak

OUT = Path(__file__).parent / "corn_main_daily.csv"

df = ak.futures_main_sina(symbol="C0")
df.columns = ["date", "open", "high", "low", "close", "volume", "open_interest", "settle"]
df["date"] = df["date"].astype(str)
df = df.sort_values("date").reset_index(drop=True)

df.to_csv(OUT, index=False, encoding="utf-8-sig")
print(f"Saved {len(df)} rows -> {OUT}")
print(df.tail())
