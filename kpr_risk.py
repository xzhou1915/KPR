import openpyxl

FILE = "sample.xlsx"

wb = openpyxl.load_workbook(FILE, data_only=True)

# --- Tenor curve ---
ws_curve = wb["sample"]
rows_curve = list(ws_curve.iter_rows(values_only=True))[1:]  # skip header
# columns: Date, Ticker, Days, Value
tenors = [(row[2], row[1]) for row in rows_curve]  # [(days, ticker), ...]
tenor_days   = [t[0] for t in tenors]
tenor_labels = [t[1] for t in tenors]

# Build interval buckets: Spot-1W, 1W-1M, ...
def short_label(ticker):
    """CNH1M Curncy -> 1M,  CNH Curncy -> Spot"""
    name = ticker.replace(" Curncy", "").replace("CNH", "")
    return name if name else "Spot"

intervals = []
for i in range(len(tenors) - 1):
    lo_days  = tenor_days[i]
    hi_days  = tenor_days[i + 1]
    label    = f"{short_label(tenor_labels[i])}-{short_label(tenor_labels[i+1])}"
    intervals.append((lo_days, hi_days, label))
# Last bucket: 2Y+
intervals.append((tenor_days[-1], float("inf"), f"{short_label(tenor_labels[-1])}+"))

# --- Exposure ---
ws_exp = wb["Exposure"]
rows_exp = list(ws_exp.iter_rows(values_only=True))[1:]  # skip header

spot_delta = 0.0
bucket_risk = {iv[2]: 0.0 for iv in intervals}

for date, value_date, usd_exp in rows_exp:
    if usd_exp is None:
        continue

    days = (value_date - date).days
    spot_delta += usd_exp

    for lo, hi, label in intervals:
        if lo <= days < hi:
            bucket_risk[label] += usd_exp
            break
    else:
        # beyond last bucket
        bucket_risk[intervals[-1][2]] += usd_exp

# --- Output ---
W = 42
print("=" * W)
print("  USDCNH Forward Portfolio Risk")
print("=" * W)
print(f"\n  Spot Delta:  ${spot_delta:>15,.0f}\n")
print("  Bucket Points Risk (USD notional):")
print(f"  {'Bucket':<14} {'Notional':>15}")
print(f"  {'-'*14} {'-'*15}")
for label, risk in bucket_risk.items():
    print(f"  {label:<14} ${risk:>14,.0f}")
print(f"\n  {'Total':<14} ${sum(bucket_risk.values()):>14,.0f}")
print("=" * W)
