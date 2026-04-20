import csv
from datetime import datetime, date
import pandas as pd

FILE     = "USDCNH.csv"
AS_OF    = date(2026, 4, 16)
CCY      = "USDCNH"

NODES = [
    ("Spot", 0),
    ("2W",   14),
    ("1M",   30),
    ("3M",   90),
    ("6M",   180),
    ("1Y",   360),
    ("2Y",   720),
    ("3Y",   1080),
]
node_names = [n[0] for n in NODES]
node_days  = [n[1] for n in NODES]

spot_delta = 0.0
node_exp   = {n: 0.0 for n in node_names}

with open(FILE, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        value_dt = datetime.strptime(row["ValueDT"], "%d/%m/%Y").date()
        notional = float(row["NetAmount1"])
        days     = (value_dt - AS_OF).days

        spot_delta += notional

        if days <= node_days[0]:
            node_exp[node_names[0]] += notional
        elif days >= node_days[-1]:
            node_exp[node_names[-1]] += notional
        else:
            for i in range(len(node_days) - 1):
                lo, hi = node_days[i], node_days[i + 1]
                if lo <= days <= hi:
                    w_hi = (days - lo) / (hi - lo)
                    node_exp[node_names[i]]     += notional * (1 - w_hi)
                    node_exp[node_names[i + 1]] += notional * w_hi
                    break

# Reverse cumulative sum → segment risk
segment_exp = {}
running = 0.0
for i in range(len(NODES) - 1, 0, -1):
    running += node_exp[node_names[i]]
    segment_exp[f"{node_names[i-1]}-{node_names[i]}"] = running
ordered = list(reversed(list(segment_exp.items())))

# --- Output ---
rows = [{"Bucket": "Spot Delta", CCY: spot_delta}]
rows += [{"Bucket": label, CCY: exp} for label, exp in ordered]
df = pd.DataFrame(rows).set_index("Bucket")

print(f"\nAs-of: {AS_OF}  |  USDCNH Forward Portfolio Risk\n")
print(df.to_string())
