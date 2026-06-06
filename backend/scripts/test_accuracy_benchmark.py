"""Phase 6: Year-by-year accuracy benchmark.

For each target year [2023, 2024, 2025]:
  Train on all prior years (2022+) → predict target → compare to actual.

Note: 2021 excluded (incompatible rank metric — community rank ≠ overall rank).
"""
import sys
import numpy as np
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR  = BASE_DIR / "data" / "cleaned"

YEAR_WEIGHT_BASE = 2019
DAMP             = 0.3
SEG_THRESHOLD    = 10000
MIN_YEAR         = 2022


def fit_predict(years, values, target_year):
    """Damped weighted linear extrapolation (mirrors build_cutoff_model.py)."""
    years  = np.asarray(years,  dtype=float)
    values = np.asarray(values, dtype=float)
    n      = len(values)
    if n == 0:
        return None
    last  = values[-1]
    vmin, vmax = values.min(), values.max()
    lo_clamp, hi_clamp = max(1.0, 0.3 * vmin), 3.0 * vmax

    if n == 1 or len(np.unique(years)) < 2:
        return int(round(last))
    if last < SEG_THRESHOLD:
        return int(round(last))

    w = years - YEAR_WEIGHT_BASE
    slope, intercept = np.polyfit(years, values, 1, w=w)
    raw  = slope * target_year + intercept
    pred = last + DAMP * (raw - last)
    pred = float(np.clip(pred, lo_clamp, hi_clamp))
    return int(round(max(1.0, pred)))


def validate_year(grp, target_year):
    """Return (all_mae, comp_mae, within_500_pct, n_all, n_comp)."""
    all_e, comp_e = [], []

    for (cc, bc, comm), g in grp:
        by_year = dict(zip(g["year"].astype(int), g["closing_rank"].astype(float)))
        if target_year not in by_year:
            continue
        train_yrs = sorted(y for y in by_year if y < target_year)
        if not train_yrs:
            continue
        pred = fit_predict(train_yrs, [by_year[y] for y in train_yrs], target_year)
        if pred is None:
            continue
        actual = int(by_year[target_year])
        e = abs(pred - actual)
        all_e.append(e)
        if actual < 10000:
            comp_e.append(e)

    all_e  = np.array(all_e,  dtype=float)
    comp_e = np.array(comp_e, dtype=float)

    all_mae  = all_e.mean()  if len(all_e)  else float("nan")
    comp_mae = comp_e.mean() if len(comp_e) else float("nan")
    comp_rmse  = np.sqrt((comp_e**2).mean()) if len(comp_e) else float("nan")
    within_500 = (comp_e <= 500).mean() * 100 if len(comp_e) else float("nan")

    return all_mae, comp_mae, comp_rmse, within_500, len(all_e), len(comp_e)


def train_label(target_year):
    years = list(range(MIN_YEAR, target_year))
    if len(years) == 1:
        return str(years[0])
    return f"{years[0]}–{years[-1]}"


def main():
    print("=" * 72)
    print("PHASE 6: YEAR-BY-YEAR ACCURACY BENCHMARK")
    print("=" * 72)
    print("Note: 2021 excluded (community rank ≠ overall rank — incompatible metric)")

    cut = pd.read_csv(DATA_DIR / "cutoffs.csv")
    cut["community"] = cut["community"].replace("BCM", "BC")
    cut = cut[cut["year"] >= MIN_YEAR].copy()
    cut = cut.groupby(
        ["college_code", "branch_code", "community", "year"], as_index=False
    ).agg(closing_rank=("closing_rank", "max"))

    grp = cut.groupby(["college_code", "branch_code", "community"])

    target_years = [y for y in [2023, 2024, 2025] if y in cut["year"].unique()]
    if not target_years:
        print("ERROR: No target years found in cutoffs.csv")
        return

    print(f"\n{'Year':>6} {'Train':>9} {'Test':>6} {'All MAE':>10} "
          f"{'Comp MAE':>10} {'Comp RMSE':>11} {'Within±500':>12} {'n_comp':>8}")
    print("-" * 72)

    rows = []
    for yr in target_years:
        all_mae, comp_mae, comp_rmse, w500, n_all, n_comp = validate_year(grp, yr)
        rows.append((yr, all_mae, comp_mae, comp_rmse, w500, n_all, n_comp))
        tl = train_label(yr)
        print(f"{yr:>6} {tl:>9} {yr:>6} {all_mae:>10.0f} "
              f"{comp_mae:>10.0f} {comp_rmse:>11.0f} {w500:>11.1f}% {n_comp:>8,}")

    print("-" * 72)

    # Trend analysis
    if len(rows) >= 2:
        comp_maes = [r[2] for r in rows if not np.isnan(r[2])]
        if len(comp_maes) >= 2:
            trend = comp_maes[-1] - comp_maes[0]
            if trend <= 0:
                trend_str = f"✅ Improving (Δ={trend:.0f})"
            elif trend < 200:
                trend_str = f"⚠️  Stable (Δ={trend:+.0f})"
            else:
                trend_str = f"❌ Degrading (Δ={trend:+.0f})"
            print(f"\nCompetitive MAE trend: {trend_str}")

    # Best/worst year
    if rows:
        best = min(rows, key=lambda r: r[2] if not np.isnan(r[2]) else float("inf"))
        worst = max(rows, key=lambda r: r[2] if not np.isnan(r[2]) else -1)
        print(f"Best year  : {best[0]} (comp MAE={best[2]:.0f})")
        print(f"Worst year : {worst[0]} (comp MAE={worst[2]:.0f})")

    final_comp = rows[-1][2] if rows else float("nan")
    print(f"\n{'='*72}")
    if np.isnan(final_comp):
        print("VERDICT: ⚠️  Insufficient data for final year")
    elif final_comp < 500:
        print(f"VERDICT: ✅ Latest year competitive MAE = {final_comp:.0f} (< 500)")
    elif final_comp < 1000:
        print(f"VERDICT: ⚠️  Latest year competitive MAE = {final_comp:.0f} (< 1000, ACCEPTABLE)")
    else:
        print(f"VERDICT: ❌ Latest year competitive MAE = {final_comp:.0f} (> 1000)")
    print(f"{'='*72}")


if __name__ == "__main__":
    main()
