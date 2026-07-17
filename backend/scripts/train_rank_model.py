
import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.interpolate import interp1d
from scipy.stats import linregress

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data" / "cleaned"

# ── Year configuration ────────────────────────────────────────────────────────
# PRIMARY_YEAR = the current admission year. Its published mark distribution is
#   the PRIMARY CDF (marks are released before ranks -> valid input feature).
# Training (historical fallback) uses every year strictly before PRIMARY_YEAR.
PRIMARY_YEAR = 2026
ANOMALY_YEARS = [2023]          # excluded from trend fitting (marks collapsed)
# Historical-fallback weights: recent years weigh more; 2023 stays tiny.
YEAR_WEIGHTS = {2022: 0.10, 2023: 0.05, 2024: 0.25, 2025: 0.60}
DEFAULT_WEIGHT = 0.33

print("=" * 80)
print(f"TRAINING RANK PREDICTION MODEL  (primary year = {PRIMARY_YEAR})")
print("=" * 80)

ranks_df = pd.read_csv(DATA_DIR / "ranks.csv")
ranks_df["community"] = ranks_df["community"].replace("BCM", "BC")

train_df = ranks_df[ranks_df["year"] < PRIMARY_YEAR].copy()
test_primary = ranks_df[ranks_df["year"] == PRIMARY_YEAR].copy()
if test_primary.empty:
    raise SystemExit(f"No rows for PRIMARY_YEAR={PRIMARY_YEAR} in ranks.csv")

COMMUNITIES = sorted(train_df["community"].unique())
YEARS = sorted(train_df["year"].unique())
TREND_YEARS = [y for y in YEARS if y not in ANOMALY_YEARS]

print(f"\nTraining years: {YEARS}  (trend from: {TREND_YEARS})")
for yr in YEARS:
    sub = train_df[train_df["year"] == yr]
    print(f"  {yr}: {len(sub):,} students, mean mark={sub['aggregate_mark'].mean():.2f}")
print(f"Primary {PRIMARY_YEAR}: {len(test_primary):,} students, "
      f"mean={test_primary['aggregate_mark'].mean():.2f}")

total_per_year = train_df.groupby("year").size().to_dict()
total_primary = len(test_primary)

# ── Mark shift model ────────────────────────────────────────────────────────────
# Marks are INPUT FEATURES — known before ranks are released.
# So we CAN use the actual PRIMARY_YEAR mark distribution for calibration.
# For each community: weighted historical mean mark vs primary-year actual mean.
# delta = actual_primary_mean - weighted_historical_mean
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
        w = YEAR_WEIGHTS.get(yr, DEFAULT_WEIGHT)
        ws += w * sub["aggregate_mark"].mean()
        total_w += w
    hist_mean[comm] = ws / total_w if total_w > 0 else 140.0

# Trend-based estimate of the primary-year mean (training data only — honest val)
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
        estimated_primary_mean = slope * PRIMARY_YEAR + intercept
        trend_based_delta[comm] = estimated_primary_mean - hist_mean[comm]
    else:
        trend_based_delta[comm] = 0.0

# Actual primary-year mean (uses input mark features only, not ranks)
actual_primary_mean = {}
actual_delta = {}
for comm in COMMUNITIES:
    sub = test_primary[test_primary["community"] == comm]
    actual_primary_mean[comm] = sub["aggregate_mark"].mean()
    actual_delta[comm] = actual_primary_mean[comm] - hist_mean[comm]

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
        w = YEAR_WEIGHTS.get(year, DEFAULT_WEIGHT)
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

for idx, row in test_primary.iterrows():
    mark = row["aggregate_mark"]
    comm = row["community"]
    actual_rank = row["rank"]

    nr_none = get_norm_rank(mark, 0.0)
    nr_trend = get_norm_rank(mark, trend_based_delta.get(comm, 0.0))
    nr_actual = get_norm_rank(mark, actual_delta.get(comm, 0.0))

    err_none.append(abs(max(1, int(nr_none * total_primary)) - actual_rank))
    err_trend.append(abs(max(1, int(nr_trend * total_primary)) - actual_rank))
    err_actual.append(abs(max(1, int(nr_actual * total_primary)) - actual_rank))

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
print(f"  actual-delta uses known {PRIMARY_YEAR} mark distribution -> valid for production")
print(f"  trend-delta uses only historical data -> conservative estimate")

# ── Compute hybrid delta (max of comm and overall) ────────────────────────────
print("\n" + "=" * 80)
print("COMPUTING HYBRID DELTA (max of comm-specific and overall)")
print("=" * 80)

overall_hist_mean = sum(
    YEAR_WEIGHTS.get(yr, DEFAULT_WEIGHT) * train_df[train_df["year"] == yr]["aggregate_mark"].mean()
    for yr in YEARS
) / sum(YEAR_WEIGHTS.get(yr, DEFAULT_WEIGHT) for yr in YEARS)

overall_actual_primary_mean = test_primary["aggregate_mark"].mean()
overall_actual_delta = overall_actual_primary_mean - overall_hist_mean

# overall trend delta as weighted avg of per-comm trends (weighted by latest
# training-year community sizes)
latest_train = max(YEARS)
total_latest = len(train_df[train_df["year"] == latest_train])
overall_trend_delta = sum(
    len(train_df[(train_df["year"] == latest_train) & (train_df["community"] == c)]) / total_latest
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
    print(f"    {comm}: actual={actual_delta.get(comm,0):.2f} -> hybrid={hybrid_actual_delta[comm]:.2f} | "
          f"trend={trend_based_delta.get(comm,0):.2f} -> hybrid={hybrid_trend_delta[comm]:.2f}")

# Validate hybrid
err_hybrid_actual = []
err_hybrid_trend = []
for idx, row in test_primary.iterrows():
    mark = row["aggregate_mark"]
    comm = row["community"]
    actual_rank = row["rank"]

    d_a = hybrid_actual_delta.get(comm, 0.0)
    d_t = hybrid_trend_delta.get(comm, 0.0)

    nr_a = get_norm_rank(mark, d_a)
    nr_t = get_norm_rank(mark, d_t)

    err_hybrid_actual.append(abs(max(1, int(nr_a * total_primary)) - actual_rank))
    err_hybrid_trend.append(abs(max(1, int(nr_t * total_primary)) - actual_rank))

err_hybrid_actual = np.array(err_hybrid_actual)
err_hybrid_trend = np.array(err_hybrid_trend)

mae_hybrid_actual = err_hybrid_actual.mean()
mae_hybrid_trend = err_hybrid_trend.mean()

print(f"\n  Hybrid actual-delta  MAE: {mae_hybrid_actual:.0f}")
print(f"  Hybrid trend-delta   MAE: {mae_hybrid_trend:.0f}")
print(f"  (vs comm-specific actual: {mae_actual:.0f}  trend: {mae_trend:.0f})")

# ── Build primary-year CDF lookup (uses marks only, not ranks) ────────────────
# Marks are published before TNEA ranks → valid to use in production.
# For each rounded mark: count students with strictly higher mark.
# pred_rank = count_above + 1  (bounded by tie-group sizes)
print("\n" + "=" * 80)
print(f"BUILDING {PRIMARY_YEAR} MARK CDF LOOKUP (mark-only, no labels)")
print("=" * 80)

primary_marks = test_primary.copy()
primary_marks["mark_rounded"] = (primary_marks["aggregate_mark"] * 2).round() / 2
all_marks_primary = sorted(primary_marks["mark_rounded"].unique())

mark_count_above = {}  # {mark_rounded: count of students with strictly higher mark}
cumulative = 0
for mark in reversed(all_marks_primary):
    cnt = (primary_marks["mark_rounded"] == mark).sum()
    mark_count_above[mark] = cumulative
    cumulative += cnt

cdf_errors = []
for idx, row in test_primary.iterrows():
    mr = round(row["aggregate_mark"] * 2) / 2
    pred = mark_count_above.get(mr, 0) + 1
    cdf_errors.append(abs(pred - row["rank"]))
cdf_errors = np.array(cdf_errors)
mae_cdf = cdf_errors.mean()

print(f"  Mark points in CDF: {len(mark_count_above)}")
print(f"  CDF approach MAE: {mae_cdf:.0f}  "
      f"(within +/-500: {(cdf_errors<=500).mean()*100:.1f}%  "
      f"+/-1000: {(cdf_errors<=1000).mean()*100:.1f}%)")
print(f"  Hybrid-delta MAE: {mae_hybrid_actual:.0f}  (fallback, no {PRIMARY_YEAR} marks needed)")

# ── Save model ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("SAVING MODEL")
print("=" * 80)

model = {
    "type": "cdf_primary_hybrid_fallback",
    "primary_year": PRIMARY_YEAR,
    "total_students_primary": total_primary,
    "communities": COMMUNITIES,
    # PRIMARY: primary-year CDF — near-perfect when current-year marks available
    "mark_count_above_primary": mark_count_above,
    "all_marks_primary_min": float(min(all_marks_primary)),
    "all_marks_primary_max": float(max(all_marks_primary)),
    # FALLBACK: historical norm_rank + hybrid shift correction
    "overall_norm_rank": overall_norm_rank,
    "overall_interp": overall_interp,
    "comm_hist_mean": hist_mean,
    "comm_trend_delta": trend_based_delta,
    "comm_actual_delta": actual_delta,
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
    "basis_label": f"percentile-based from 2022-{PRIMARY_YEAR} data",
    # ── legacy aliases (older ml_utils expected *_2025 key names) ──
    "total_students_2025": total_primary,
    "mark_count_above_2025": mark_count_above,
    "comm_actual_delta_2025": actual_delta,
}

with open(DATA_DIR / "rank_model_final.pkl", "wb") as f:
    pickle.dump(model, f)
print("  Saved: rank_model_final.pkl")

rank_meta = {
    "type": model["type"],
    "primary_year": PRIMARY_YEAR,
    "range_halfwidth": 100,
    "basis": model["basis_label"],
    "communities": COMMUNITIES,
    "train_years": YEARS,
    "total_students_primary": total_primary,
    "val_mae_cdf": mae_cdf,
    "val_mae_hybrid_actual": mae_hybrid_actual,
    "primary": f"{PRIMARY_YEAR} mark CDF lookup",
    "fallback": "historical norm_rank + hybrid delta",
}
with open(DATA_DIR / "rank_model_meta.pkl", "wb") as f:
    pickle.dump(rank_meta, f)
print("  Saved: rank_model_meta.pkl")

print(f"\nTRAINING COMPLETE  (primary year {PRIMARY_YEAR})")
print(f"  CDF-primary MAE:  {mae_cdf:.0f}")
print(f"  Trend-delta MAE (no future data): {mae_trend:.0f}")
print(f"  Actual-delta MAE (with mark stats): {mae_actual:.0f}")
