"""Correlation stability study: DCE corn (USD) vs synthetic cash series.

Diagnostics:
1. Full-sample Pearson + Spearman correlation (returns)
2. Rolling correlation: 30d and 60d
3. Sub-period split (quarterly)
4. Rolling 60d hedge ratio (beta)
5. Down-market vs up-market conditional correlation
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

DIR = Path(__file__).parent
DATA = DIR / "corn_vs_synthetic_usd.csv"

df = pd.read_csv(DATA, parse_dates=["date"]).sort_values("date").reset_index(drop=True)
df = df.dropna(subset=["dce_corn_close_usd", "synthetic"]).reset_index(drop=True)

df["corn_ret"] = np.log(df["dce_corn_close_usd"]).diff()
df["syn_ret"] = np.log(df["synthetic"]).diff()
df = df.dropna().reset_index(drop=True)

results = {}

# 1) Full sample
results["n_obs"] = len(df)
results["pearson_full"] = df["corn_ret"].corr(df["syn_ret"])
results["spearman_full"] = df["corn_ret"].corr(df["syn_ret"], method="spearman")

# 2) Rolling correlation
df["roll_corr_30"] = df["corn_ret"].rolling(30).corr(df["syn_ret"])
df["roll_corr_60"] = df["corn_ret"].rolling(60).corr(df["syn_ret"])
for w in (30, 60):
    s = df[f"roll_corr_{w}"].dropna()
    results[f"roll{w}_mean"] = s.mean()
    results[f"roll{w}_min"] = s.min()
    results[f"roll{w}_max"] = s.max()
    results[f"roll{w}_std"] = s.std()

# 3) Sub-period split (quarterly)
df["quarter"] = df["date"].dt.to_period("Q").astype(str)
sub = df.groupby("quarter").apply(
    lambda g: pd.Series({
        "n": len(g),
        "pearson": g["corn_ret"].corr(g["syn_ret"]),
        "spearman": g["corn_ret"].corr(g["syn_ret"], method="spearman"),
    })
)

# 4) Rolling 60d hedge ratio (beta): syn_ret = alpha + beta * corn_ret
def rolling_beta(y, x, window=60):
    out = pd.Series(np.nan, index=y.index, dtype=float)
    for i in range(window, len(y) + 1):
        ys = y.iloc[i - window:i].values
        xs = x.iloc[i - window:i].values
        slope, _, _, _, _ = stats.linregress(xs, ys)
        out.iloc[i - 1] = slope
    return out

df["rolling_beta_60"] = rolling_beta(df["syn_ret"], df["corn_ret"], 60)
b = df["rolling_beta_60"].dropna()
results["beta60_mean"] = b.mean()
results["beta60_min"] = b.min()
results["beta60_max"] = b.max()
results["beta60_std"] = b.std()

# 5) Down/up-market conditional correlation
down = df[df["syn_ret"] < 0]
up = df[df["syn_ret"] >= 0]
results["down_pearson"] = down["corn_ret"].corr(down["syn_ret"])
results["down_spearman"] = down["corn_ret"].corr(down["syn_ret"], method="spearman")
results["up_pearson"] = up["corn_ret"].corr(up["syn_ret"])
results["up_spearman"] = up["corn_ret"].corr(up["syn_ret"], method="spearman")
results["n_down"] = len(down)
results["n_up"] = len(up)

# Save summary
summary = pd.Series(results).round(4)
summary.to_csv(DIR / "correlation_study_summary.csv", header=["value"], encoding="utf-8-sig")
sub.round(4).to_csv(DIR / "correlation_study_quarters.csv", encoding="utf-8-sig")

print("=== Full sample ===")
print(f"n = {results['n_obs']}")
print(f"Pearson  : {results['pearson_full']:.3f}")
print(f"Spearman : {results['spearman_full']:.3f}")

print("\n=== Rolling correlation stability ===")
for w in (30, 60):
    print(f"{w}d : mean={results[f'roll{w}_mean']:.3f}  min={results[f'roll{w}_min']:.3f}  "
          f"max={results[f'roll{w}_max']:.3f}  std={results[f'roll{w}_std']:.3f}")

print("\n=== Rolling 60d beta (hedge ratio) ===")
print(f"mean={results['beta60_mean']:.3f}  min={results['beta60_min']:.3f}  "
      f"max={results['beta60_max']:.3f}  std={results['beta60_std']:.3f}")

print("\n=== Quarterly correlations ===")
print(sub.round(3))

print("\n=== Asymmetric correlation ===")
print(f"Down (syn<0, n={results['n_down']}): Pearson={results['down_pearson']:.3f}  Spearman={results['down_spearman']:.3f}")
print(f"Up   (syn>=0, n={results['n_up']}): Pearson={results['up_pearson']:.3f}  Spearman={results['up_spearman']:.3f}")

# Plots
fig = plt.figure(figsize=(14, 16))
gs = fig.add_gridspec(4, 2, height_ratios=[1, 1, 1.2, 1], hspace=0.45, wspace=0.25)
ax_roll = fig.add_subplot(gs[0, :])
ax_beta = fig.add_subplot(gs[1, :])
ax_scatter = fig.add_subplot(gs[2, 0])
ax_quart = fig.add_subplot(gs[2, 1])
ax_asym = fig.add_subplot(gs[3, 0])
ax_summary = fig.add_subplot(gs[3, 1])

# Rolling correlation
ax_roll.plot(df["date"], df["roll_corr_30"], label="30d", alpha=0.8)
ax_roll.plot(df["date"], df["roll_corr_60"], label="60d", lw=2)
ax_roll.axhline(0, color="k", lw=0.5)
ax_roll.axhline(results["pearson_full"], color="red", ls="--", lw=0.8,
                label=f"Full Pearson={results['pearson_full']:.2f}")
ax_roll.set_title("Rolling correlation (log returns)")
ax_roll.legend()
ax_roll.grid(True, alpha=0.3)

# Rolling beta
ax_beta.plot(df["date"], df["rolling_beta_60"], color="orange")
ax_beta.axhline(results["beta60_mean"], color="red", ls="--", lw=0.8,
                label=f"mean β={results['beta60_mean']:.2f}")
ax_beta.set_title("Rolling 60d hedge ratio β  (syn_ret = α + β·corn_ret)")
ax_beta.legend()
ax_beta.grid(True, alpha=0.3)

# Returns scatter
slope, intercept, r, _, _ = stats.linregress(df["corn_ret"], df["syn_ret"])
xline = np.linspace(df["corn_ret"].min(), df["corn_ret"].max(), 100)
ax_scatter.scatter(df["corn_ret"], df["syn_ret"], s=10, alpha=0.5)
ax_scatter.plot(xline, intercept + slope * xline, color="red", label=f"β={slope:.2f}  r={r:.2f}")
ax_scatter.axhline(0, color="k", lw=0.3)
ax_scatter.axvline(0, color="k", lw=0.3)
ax_scatter.set_xlabel("Corn log return")
ax_scatter.set_ylabel("Synthetic log return")
ax_scatter.set_title("Returns scatter")
ax_scatter.legend()
ax_scatter.grid(True, alpha=0.3)

# Quarterly correlation bars
quarters = sub.index.tolist()
x = np.arange(len(quarters))
w = 0.38
ax_quart.bar(x - w/2, sub["pearson"].values, w, label="Pearson", color="steelblue")
ax_quart.bar(x + w/2, sub["spearman"].values, w, label="Spearman", color="darkorange")
ax_quart.set_xticks(x)
ax_quart.set_xticklabels(quarters, rotation=30, ha="right")
ax_quart.axhline(0, color="k", lw=0.5)
ax_quart.set_title("Quarterly correlation")
ax_quart.set_ylabel("Correlation")
ax_quart.legend()
ax_quart.grid(True, axis="y", alpha=0.3)

# Asymmetric correlation bars
labels = ["Down\n(syn<0)", "Up\n(syn>=0)"]
pearson_vals = [results["down_pearson"], results["up_pearson"]]
spearman_vals = [results["down_spearman"], results["up_spearman"]]
xa = np.arange(len(labels))
ax_asym.bar(xa - w/2, pearson_vals, w, label="Pearson", color="steelblue")
ax_asym.bar(xa + w/2, spearman_vals, w, label="Spearman", color="darkorange")
ax_asym.set_xticks(xa)
ax_asym.set_xticklabels(labels)
ax_asym.axhline(0, color="k", lw=0.5)
ax_asym.axhline(results["pearson_full"], color="red", ls="--", lw=0.8,
                label=f"Full Pearson={results['pearson_full']:.2f}")
ax_asym.set_title(f"Asymmetric correlation (n_down={results['n_down']}, n_up={results['n_up']})")
ax_asym.set_ylabel("Correlation")
ax_asym.legend()
ax_asym.grid(True, axis="y", alpha=0.3)

# Summary text panel
ax_summary.axis("off")
text = (
    f"FULL SAMPLE  (n = {results['n_obs']})\n"
    f"  Pearson  : {results['pearson_full']:.3f}\n"
    f"  Spearman : {results['spearman_full']:.3f}\n\n"
    f"ROLLING CORR STABILITY\n"
    f"  30d  mean {results['roll30_mean']:.3f}  min {results['roll30_min']:.3f}  "
    f"max {results['roll30_max']:.3f}  std {results['roll30_std']:.3f}\n"
    f"  60d  mean {results['roll60_mean']:.3f}  min {results['roll60_min']:.3f}  "
    f"max {results['roll60_max']:.3f}  std {results['roll60_std']:.3f}\n\n"
    f"ROLLING 60d BETA\n"
    f"  mean {results['beta60_mean']:.3f}  min {results['beta60_min']:.3f}  "
    f"max {results['beta60_max']:.3f}  std {results['beta60_std']:.3f}"
)
ax_summary.text(0.02, 0.95, text, transform=ax_summary.transAxes,
                family="monospace", fontsize=10, va="top",
                bbox=dict(boxstyle="round,pad=0.5", facecolor="#f5f5f5", edgecolor="gray"))
ax_summary.set_title("Summary stats")

plt.savefig(DIR / "correlation_study_plots.png", dpi=120, bbox_inches="tight")
print(f"\nPlots -> correlation_study_plots.png")
print(f"Summary -> correlation_study_summary.csv")
print(f"Quarters -> correlation_study_quarters.csv")
