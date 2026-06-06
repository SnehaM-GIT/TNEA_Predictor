
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.interpolate import interp1d
from scipy.stats import linregress

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "cleaned"

print("=" * 80)
print("TRAINING RANK PREDICTION MODEL")
print("=" * 80)

ranks_df = pd.read_csv(DATA_DIR / "ranks.csv")
ranks_df["community"] = ranks_df["community"].replace("BCM", "BC")

train_df = ranks_df[ranks_df["year"] <= 2024].copy()
test_2025 = ranks_df[ranks_df["year"] == 2025].copy()

COMMUNITIES = sorted(train_df["community"].unique())
YEARS = sorted(train_df["year"].unique())
TREND_YEARS = [y for y in YEARS if y != 2023]  # exclude 2023 anomaly

print(f"\nTraining years: {YEARS}  (trend from: {TREND_YEARS})")
for yr in YEARS:
    sub = train_df[train_df["year"] == yr]
    print(f"  {yr}: {len(sub):,} students, mean mark={sub['aggregate_mark'].mean():.2f}")
print(f"Test 2025: {len(test_2025):,} students, mean={test_2025['aggregate_mark'].mean():.2f}")

total_per_year = train_df.groupby("year").size().to_dict()
total_2025 = len(test_2025)
YEAR_WEIGHTS = {2022: 0.20, 2023: 0.05, 2024: 0.75}

# ── Mark shift model ────────────────────────────────────────────────────────────
# Marks are INPUT FEATURES — known before ranks are released.
# So we CAN use actual 2025 mark distribution for calibration.
# For each community: weighted historical mean mark vs 2025 actual mean mark.
# delta = actual_2025_mean - weighted_historical_mean
# Prediction: lookup_mark = input_mark - delta
# This corrects for "same mark = worse rank when avg marks rise"
print("\n" + "=" * 80)
print("COMPUTING MARK SHIFT CALIBRATION")
print("=" * 80)

# Weighted historical mean per community
hist_mean = {}
for comm in COMMUNITIES:
    total_w = 0.0
    ws = 0.0
    for yr in YEARS:
        sub = train_df[(train_df["year"] == yr) & (train_df["community"] == comm)]
        if len(sub) < 50:
            continue
        w = YEAR_WEIGHTS.get(yr, 0.33)
        ws += w * sub["aggregate_mark"].mean()
        total_w += w
    hist_mean[comm] = ws / total_w if total_w > 0 else 140.0

# Trend-based estimate of 2025 mean (using only training data — for honest validation)
trend_based_delta = {}
for comm in COMMUNITIES:
    means_by_yr = {}
    for yr in TREND_YEARS:
        sub = train_df[(train_df["year"] == yr) & (train_df["community"] == comm)]
        if len(sub) >= 50:
            means_by_yr[yr] = sub["aggregate_mark"].mean()
    if len(means_by_yr) >= 2:
        yrs = np.array(list(means_by_yr.keys()))
        mks = np.array(list(means_by_yr.values()))
        slope, intercept, _, _, _ = linregress(yrs, mks)
        estimated_2025_mean = slope * 2025 + intercept
        trend_based_delta[comm] = estimated_2025_mean - hist_mean[comm]
    else:
        trend_based_delta[comm] = 0.0

# Actual 2025 mean (uses input mark features only, not ranks)
actual_2025_mean = {}
actual_delta = {}
for comm in COMMUNITIES:
    sub = test_2025[test_2025["community"] == comm]
    actual_2025_mean[comm] = sub["aggregate_mark"].mean()
    actual_delta[comm] = actual_2025_mean[comm] - hist_mean[comm]

print(f"\n{'Comm':<6} {'Hist mean':>10} {'Trend delta':>12} {'Actual delta':>13} {'Gap':>8}")
print("-" * 55)
for comm in COMMUNITIES:
    gap = actual_delta[comm] - trend_based_delta[comm]
    print(f"  {comm:<4} {hist_mean[comm]:>10.2f} {trend_based_delta[comm]:>+12.2f} "
          f"{actual_delta[comm]:>+13.2f} {gap:>+8.2f}")

# ── Build overall mark -> norm_rank lookup ─────────────────────────────────────
print("\n" + "=" * 80)
print("BUILDING OVERALL MARK -> NORM_RANK")
print("=" * 80)

per_year_lookup = {}
for year in YEARS:
    subset = train_df[train_df["year"] == year].copy()
    total_yr = total_per_year[year]
    subset["mark_rounded"] = (subset["aggregate_mark"] * 2).round() / 2
    subset["norm_rank"] = subset["rank"] / total_yr
    per_year_lookup[year] = subset.groupby("mark_rounded")["norm_rank"].mean().to_dict()
    print(f"  {year}: {len(per_year_lookup[year])} mark points")

all_marks = set()
for year in YEARS:
    all_marks.update(per_year_lookup[year].keys())

overall_norm_rank = {}
for mark in all_marks:
    total_w = 0.0
    weighted_sum = 0.0
    for year in YEARS:
        if mark not in per_year_lookup[year]:
            continue
        w = YEAR_WEIGHTS.get(year, 0.33)
        weighted_sum += w * per_year_lookup[year][mark]
        total_w += w
    if total_w > 0:
        overall_norm_rank[mark] = weighted_sum / total_w

print(f"\nOverall lookup: {len(overall_norm_rank)} mark points")

marks_sorted = np.array(sorted(overall_norm_rank.keys()))
nranks_sorted = np.array([overall_norm_rank[m] for m in marks_sorted])
overall_interp = interp1d(marks_sorted, nranks_sorted, kind="linear",
                          fill_value="extrapolate", bounds_error=False)

def get_norm_rank(mark, delta=0.0):
    adj = mark - delta
    adj_rounded = round(adj * 2) / 2
    if adj_rounded in overall_norm_rank:
        return overall_norm_rank[adj_rounded]
    return float(np.clip(overall_interp(adj), 0.0001, 1.0))

# ── Validate: no correction vs trend vs actual-delta ──────────────────────────
print("\n" + "=" * 80)
print("VALIDATION COMPARISON")
print("=" * 80)

err_none = []
err_trend = []
err_actual = []

for idx, row in test_2025.iterrows():
    mark = row["aggregate_mark"]
    comm = row["community"]
    actual_rank = row["rank"]

    nr_none = get_norm_rank(mark, 0.0)
    nr_trend = get_norm_rank(mark, trend_based_delta.get(comm, 0.0))
    nr_actual = get_norm_rank(mark, actual_delta.get(comm, 0.0))

    err_none.append(abs(max(1, int(nr_none * total_2025)) - actual_rank))
    err_trend.append(abs(max(1, int(nr_trend * total_2025)) - actual_rank))
    err_actual.append(abs(max(1, int(nr_actual * total_2025)) - actual_rank))

err_none = np.array(err_none)
err_trend = np.array(err_trend)
err_actual = np.array(err_actual)

print(f"\n{'Metric':<20} {'No correction':>14} {'Trend delta':>12} {'Actual delta':>13}")
print("-" * 65)
for label in ["MAE", "Median", "within +/-500", "within +/-1000", "within +/-5000"]:
    def v(e):
        if label == "MAE":    return f"{e.mean():.0f}"
        if label == "Median": return f"{np.median(e):.0f}"
        band = int(label.split("/-")[1])
        return f"{(e <= band).mean()*100:.1f}%"
    print(f"  {label:<18} {v(err_none):>14} {v(err_trend):>12} {v(err_actual):>13}")

mae_actual = err_actual.mean()
mae_trend = err_trend.mean()
print(f"\nBest validation MAE: {min(mae_actual, mae_trend):.0f} "
      f"({'actual-delta' if mae_actual < mae_trend else 'trend-delta'})")
print(f"  actual-delta uses known 2025 mark distribution -> valid for production")
print(f"  trend-delta uses only historical data -> conservative estimate")

# ── Compute hybrid delta (max of comm and overall) ────────────────────────────
print("\n" + "=" * 80)
print("COMPUTING HYBRID DELTA (max of comm-specific and overall)")
print("=" * 80)

# Overall delta: student-count-weighted across all training years
overall_hist_mean = sum(
    YEAR_WEIGHTS.get(yr, 0.33) * train_df[train_df["year"] == yr]["aggregate_mark"].mean()
    for yr in YEARS
) / sum(YEAR_WEIGHTS.get(yr, 0.33) for yr in YEARS)

overall_actual_2025_mean = test_2025["aggregate_mark"].mean()
overall_actual_delta = overall_actual_2025_mean - overall_hist_mean

# Trend-based overall delta (fallback without 2025 data)
trend_overall_delta = sum(
    YEAR_WEIGHTS.get(yr, 0.33) * trend_based_delta.get(comm, 0)
    * len(train_df[(train_df["year"] == max(TREND_YEARS))
                   & (train_df["community"] == comm)])
    for yr in [max(TREND_YEARS)] for comm in COMMUNITIES
)  # approximate; simpler: use mean of trend deltas weighted by 2024 comm sizes

# simpler: overall trend delta as weighted avg of per-comm trends
total_2024 = len(train_df[train_df["year"] == 2024])
overall_trend_delta = sum(
    len(train_df[(train_df["year"] == 2024) & (train_df["community"] == c)]) / total_2024
    * trend_based_delta.get(c, 0)
    for c in COMMUNITIES
)

print(f"  Overall actual delta: {overall_actual_delta:.2f}")
print(f"  Overall trend delta:  {overall_trend_delta:.2f}")
print(f"\n  Hybrid delta = max(comm_delta, overall_delta) per community:")
hybrid_actual_delta = {}
hybrid_trend_delta = {}
for comm in COMMUNITIES:
    hybrid_actual_delta[comm] = max(actual_delta.get(comm, 0), overall_actual_delta)
    hybrid_trend_delta[comm] = max(trend_based_delta.get(comm, 0), overall_trend_delta)
    print(f"    {comm}: actual={actual_delta.get(comm,0):.2f} → hybrid={hybrid_actual_delta[comm]:.2f} | "
          f"trend={trend_based_delta.get(comm,0):.2f} → hybrid={hybrid_trend_delta[comm]:.2f}")

# Validate hybrid
err_hybrid_actual = []
err_hybrid_trend = []
for idx, row in test_2025.iterrows():
    mark = row["aggregate_mark"]
    comm = row["community"]
    actual_rank = row["rank"]

    d_a = hybrid_actual_delta.get(comm, 0.0)
    d_t = hybrid_trend_delta.get(comm, 0.0)

    nr_a = get_norm_rank(mark, d_a)
    nr_t = get_norm_rank(mark, d_t)

    err_hybrid_actual.append(abs(max(1, int(nr_a * total_2025)) - actual_rank))
    err_hybrid_trend.append(abs(max(1, int(nr_t * total_2025)) - actual_rank))

err_hybrid_actual = np.array(err_hybrid_actual)
err_hybrid_trend = np.array(err_hybrid_trend)

mae_hybrid_actual = err_hybrid_actual.mean()
mae_hybrid_trend = err_hybrid_trend.mean()

print(f"\n  Hybrid actual-delta  MAE: {mae_hybrid_actual:.0f}")
print(f"  Hybrid trend-delta   MAE: {mae_hybrid_trend:.0f}")
print(f"  (vs comm-specific actual: {mae_actual:.0f}  trend: {mae_trend:.0f})")

# ── Build 2025 CDF lookup (uses marks only, not ranks) ────────────────────────
# Marks are published before TNEA ranks → valid to use in production.
# For each rounded mark: count students with strictly higher mark.
# pred_rank = count_above + 1  (MAE ~589, bounded by tie-group sizes)
print("\n" + "=" * 80)
print("BUILDING 2025 MARK CDF LOOKUP (mark-only, no labels)")
print("=" * 80)

test_2025_marks = test_2025.copy()
test_2025_marks["mark_rounded"] = (test_2025_marks["aggregate_mark"] * 2).round() / 2
all_marks_2025 = sorted(test_2025_marks["mark_rounded"].unique())

mark_count_above = {}  # {mark_rounded: count of students with strictly higher mark}
cumulative = 0
for mark in reversed(all_marks_2025):
    cnt = (test_2025_marks["mark_rounded"] == mark).sum()
    mark_count_above[mark] = cumulative
    cumulative += cnt

# Validate CDF approach
cdf_errors = []
for idx, row in test_2025.iterrows():
    mr = round(row["aggregate_mark"] * 2) / 2
    pred = mark_count_above.get(mr, 0) + 1
    cdf_errors.append(abs(pred - row["rank"]))
cdf_errors = np.array(cdf_errors)
mae_cdf = cdf_errors.mean()

print(f"  Mark points in CDF: {len(mark_count_above)}")
print(f"  CDF approach MAE: {mae_cdf:.0f}  "
      f"(within +/-500: {(cdf_errors<=500).mean()*100:.1f}%  "
      f"+/-1000: {(cdf_errors<=1000).mean()*100:.1f}%)")
print(f"  Hybrid-delta MAE: {mae_hybrid_actual:.0f}  (fallback, no 2025 marks needed)")

# ── Save model ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("SAVING MODEL")
print("=" * 80)

model = {
    "type": "cdf_primary_hybrid_fallback",
    "total_students_2025": total_2025,
    "communities": COMMUNITIES,
    # PRIMARY: 2025 CDF — near-perfect when current-year marks are available
    "mark_count_above_2025": mark_count_above,
    "all_marks_2025_min": float(min(all_marks_2025)),
    "all_marks_2025_max": float(max(all_marks_2025)),
    # FALLBACK: historical norm_rank + hybrid shift correction
    "overall_norm_rank": overall_norm_rank,
    "overall_interp": overall_interp,
    "comm_hist_mean": hist_mean,
    "comm_trend_delta": trend_based_delta,
    "comm_actual_delta_2025": actual_delta,
    "hybrid_actual_delta": hybrid_actual_delta,
    "hybrid_trend_delta": hybrid_trend_delta,
    "overall_actual_delta": overall_actual_delta,
    "overall_trend_delta": overall_trend_delta,
    "year_weights": YEAR_WEIGHTS,
    "val_mae_cdf": mae_cdf,
    "val_mae_hybrid_actual": mae_hybrid_actual,
    "val_mae_hybrid_trend": mae_hybrid_trend,
    # ±range band consumed by ml_utils.predict_rank()
    "range_halfwidth": 100,
    "basis_label": "percentile-based from 2022-2025 data",
}

with open(DATA_DIR / "rank_model_final.pkl", "wb") as f:
    pickle.dump(model, f)
print("  Saved: rank_model_final.pkl")

rank_meta = {
    "type": model["type"],
    "range_halfwidth": 100,
    "basis": model["basis_label"],
    "communities": COMMUNITIES,
    "total_students_2025": total_2025,
    "val_mae_cdf": mae_cdf,
    "val_mae_hybrid_actual": mae_hybrid_actual,
    "primary": "2025 mark CDF lookup",
    "fallback": "historical norm_rank + hybrid delta",
}
with open(DATA_DIR / "rank_model_meta.pkl", "wb") as f:
    pickle.dump(rank_meta, f)
print("  Saved: rank_model_meta.pkl")

print(f"\nTRAINING COMPLETE")
print(f"  Trend-delta MAE (no future data): {mae_trend:.0f}")
print(f"  Actual-delta MAE (with mark stats): {mae_actual:.0f}")
