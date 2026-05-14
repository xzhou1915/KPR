"""Build DCE corn close in USD vs synthetic cash series, from 2024-12-10."""
from pathlib import Path
import numpy as np
import pandas as pd
import akshare as ak

OUT = Path(__file__).parent / "corn_vs_synthetic_usd.csv"
START = "2024-12-10"

corn = ak.futures_main_sina(symbol="C0")
corn.columns = ["date", "open", "high", "low", "close", "volume", "open_interest", "settle"]
corn["date"] = pd.to_datetime(corn["date"].astype(str))
corn = corn[["date", "close"]].rename(columns={"close": "close_rmb"})

fx = ak.currency_boc_sina(symbol="美元", start_date="20241201", end_date=pd.Timestamp.today().strftime("%Y%m%d"))
fx = fx.rename(columns={"日期": "date", "中行汇买价": "usdcny"})
fx["date"] = pd.to_datetime(fx["date"])
fx = fx[["date", "usdcny"]].sort_values("date")
fx["usdcny"] = fx["usdcny"].astype(float) / 100.0

df = corn.merge(fx, on="date", how="left")
df["usdcny"] = df["usdcny"].ffill()
df["dce_corn_close_usd"] = (df["close_rmb"] / df["usdcny"]).round(2)

df = df[df["date"] >= pd.Timestamp(START)].reset_index(drop=True)

rng = np.random.default_rng(42)
n = len(df)
base = df["dce_corn_close_usd"].values
noise = rng.normal(0, 3, n).cumsum()
df["synthetic"] = (base * 0.7 + 80 + noise).round(2)

out = df[["date", "close_rmb", "dce_corn_close_usd", "synthetic"]].rename(
    columns={"close_rmb": "dce_corn_close_cny"}
)
out["date"] = out["date"].dt.strftime("%Y-%m-%d")
out.to_csv(OUT, index=False, encoding="utf-8-sig")

print(f"Saved {len(out)} rows -> {OUT}")
print(out.head())
print("...")
print(out.tail())
