"""Phase 2: Cutoff model comprehensive validation.

Re-runs the build_cutoff_model validation logic:
  Train on 2022-2024 data → predict 2025 → compare to actual 2025 cutoffs.
Reports MAE / RMSE / within-band metrics per community and overall.
"""
import sys
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"

COMMUNITIES   = ["OC", "BC", "SC", "ST", "MBC", "SCA"]
YEAR_WEIGHT_BASE = 2019
DAMP          = 0.3
SEG_THRESHOLD = 10000
MIN_YEAR      = 2022   # 2021 excluded: incompatible rank metric


def fit_predict(years, values, target_year):
    """Damped weighted linear extrapolation (mirrors build_cutoff_model.py)."""
    years  = np.asarray(years,  dtype=float)
    values = np.asarray(values, dtype=float)
    n      = len(values)
    if n == 0:
        return None
    last = values[-1]
    vmin, vmax = values.min(), values.max()
    lo_clamp   = max(1.0, 0.3 * vmin)
    hi_clamp   = 3.0 * vmax

    if n == 1 or len(np.unique(years)) < 2:
        return int(round(last))
    if last < SEG_THRESHOLD:      # persistence wins for competitive seats
        return int(round(last))

    w = years - YEAR_WEIGHT_BASE
    slope, intercept = np.polyfit(years, values, 1, w=w)
    raw  = slope * target_year + intercept
    pred = last + DAMP * (raw - last)
    pred = float(np.clip(pred, lo_clamp, hi_clamp))
    return int(round(max(1.0, pred)))


def main():
    print("=" * 70)
    print("PHASE 2: CUTOFF MODEL COMPREHENSIVE VALIDATION")
    print("Train 2022-2024  →  Predict 2025  →  Compare to actual 2025")
    print("=" * 70)

    # ── load & clean ─────────────────────────────────────────────────────────
    print("\nLoading cutoffs.csv ...")
    cut = pd.read_csv(DATA_DIR / "cutoffs.csv")
    cut["community"] = cut["community"].replace("BCM", "BC")
    total_raw = len(cut)
    cut = cut[cut["year"] >= MIN_YEAR].copy()
    cut = cut.groupby(
        ["college_code", "branch_code", "community", "year"], as_index=False
    ).agg(closing_rank=("closing_rank", "max"))
    print(f"  Raw rows: {total_raw:,}  |  After 2021 exclusion + collapse: {len(cut):,}")

    grp = cut.groupby(["college_code", "branch_code", "community"])

    # ── run validation ───────────────────────────────────────────────────────
    errs_all  = {c: [] for c in COMMUNITIES}
    errs_comp = {c: [] for c in COMMUNITIES}
    all_err, comp_err, top_err = [], [], []
    worst_comp, best_comp = [], []

    for (cc, bc, comm), g in grp:
        by_year = dict(zip(g["year"].astype(int), g["closing_rank"].astype(float)))
        if 2025 not in by_year:
            continue
        train_yrs = sorted(y for y in by_year if y <= 2024)
        if not train_yrs:
            continue
        pred = fit_predict(train_yrs, [by_year[y] for y in train_yrs], 2025)
        if pred is None:
            continue
        actual = int(by_year[2025])
        e = abs(pred - actual)
        all_err.append(e)

        if comm in errs_all:
            errs_all[comm].append(e)

        if actual < 10000:
            comp_err.append(e)
            if comm in errs_comp:
                errs_comp[comm].append(e)
            worst_comp.append((e, cc, bc, comm, pred, actual))
            best_comp.append((e, cc, bc, comm, pred, actual))

        if actual < 5000:
            top_err.append(e)

    all_err  = np.array(all_err,  dtype=float)
    comp_err = np.array(comp_err, dtype=float)
    top_err  = np.array(top_err,  dtype=float)

    # ── community table (competitive segment) ────────────────────────────────
    print(f"\nCOMPETITIVE SEGMENT (actual 2025 closing_rank < 10 000)")
    print(f"{'Community':<12}{'Count':>8}{'MAE':>10}{'RMSE':>10}"
          f"{'Within±500':>12}{'Within±1000':>13}")
    print("-" * 65)

    for comm in COMMUNITIES:
        e = np.array(errs_comp[comm], dtype=float)
        if len(e) == 0:
            print(f"{comm:<12}{'0':>8}  (no data)")
            continue
        mae  = e.mean()
        rmse = np.sqrt((e**2).mean())
        p500  = (e <= 500).mean()  * 100
        p1000 = (e <= 1000).mean() * 100
        flag  = "OK" if mae < 1000 else ("ACCEPT" if mae < 2000 else "WEAK")
        print(f"{comm:<12}{len(e):>8,}{mae:>10.0f}{rmse:>10.0f}"
              f"{p500:>11.1f}%{p1000:>12.1f}%  {flag}")

    print("-" * 65)
    if len(comp_err):
        cmae  = comp_err.mean()
        crmse = np.sqrt((comp_err**2).mean())
        cp500  = (comp_err <= 500).mean()  * 100
        cp1000 = (comp_err <= 1000).mean() * 100
        print(f"{'ALL (comp)':<12}{len(comp_err):>8,}{cmae:>10.0f}{crmse:>10.0f}"
              f"{cp500:>11.1f}%{cp1000:>12.1f}%")
    else:
        cmae = float("inf")

    print(f"\nFull set (all combos incl. noisy low-demand tail):")
    print(f"  MAE={all_err.mean():.0f}  RMSE={np.sqrt((all_err**2).mean()):.0f}  "
          f"n={len(all_err):,}")
    if len(top_err):
        print(f"  Top <5000 MAE={top_err.mean():.0f}  n={len(top_err):,}")

    # ── percentile errors ────────────────────────────────────────────────────
    print(f"\nError percentiles (competitive segment):")
    for p in [25, 50, 75, 90, 95]:
        print(f"  {p}th percentile: {np.percentile(comp_err, p):.0f}")

    p100 = (comp_err <= 100).mean() * 100
    p200 = (comp_err <= 200).mean() * 100
    print(f"\nWithin ±100:  {p100:.1f}%")
    print(f"Within ±200:  {p200:.1f}%")
    print(f"Within ±500:  {cp500:.1f}%")
    print(f"Within ±1000: {cp1000:.1f}%")

    # ── worst 10 ─────────────────────────────────────────────────────────────
    worst_comp.sort(key=lambda x: -x[0])
    print(f"\nWorst 10 predictions (competitive segment):")
    print(f"  {'Error':>8}  {'Code':>6}  {'Branch':>10}  {'Comm':>5}  {'Pred':>8}  {'Actual':>8}")
    for e, cc, bc, comm, pred, actual in worst_comp[:10]:
        print(f"  {e:>8,}  {cc:>6}  {str(bc):>10}  {comm:>5}  {pred:>8,}  {actual:>8,}")

    best_comp.sort(key=lambda x: x[0])
    print(f"\nBest 10 predictions (competitive segment):")
    print(f"  {'Error':>8}  {'Code':>6}  {'Branch':>10}  {'Comm':>5}  {'Pred':>8}  {'Actual':>8}")
    for e, cc, bc, comm, pred, actual in best_comp[:10]:
        print(f"  {e:>8,}  {cc:>6}  {str(bc):>10}  {comm:>5}  {pred:>8,}  {actual:>8,}")

    # ── also check saved meta ─────────────────────────────────────────────────
    meta_path = DATA_DIR / "cutoff_model_meta.pkl"
    if meta_path.exists():
        with open(meta_path, "rb") as f:
            meta = pickle.load(f)
        print(f"\nSaved model meta (from cutoff_model_meta.pkl):")
        print(f"  val_competitive_mae : {meta.get('val_competitive_mae', '?')}")
        print(f"  val_top5000_mae     : {meta.get('val_top5000_mae', '?')}")
        print(f"  val_full_mae        : {meta.get('val_full_mae', '?')}")
        print(f"  within_500_pct      : {meta.get('competitive_within_500_pct', '?')}%")
        print(f"  within_1000_pct     : {meta.get('competitive_within_1000_pct', '?')}%")
        print(f"  n_combos            : {meta.get('n_combos', '?'):,}")

    # ── verdict ───────────────────────────────────────────────────────────────
    print(f"\n{'='*70}")
    if cmae < 300:
        verdict = "✅ EXCELLENT (competitive MAE < 300)"
    elif cmae < 500:
        verdict = "✅ GOOD (competitive MAE < 500)"
    elif cmae < 1000:
        verdict = "⚠️  ACCEPTABLE (competitive MAE < 1000)"
    else:
        verdict = "❌ NEEDS WORK (competitive MAE > 1000)"
    print(f"VERDICT: {verdict}")
    print(f"  Competitive MAE : {cmae:.0f} ranks")
    print(f"  Within ±500     : {cp500:.1f}%")
    print(f"  Within ±1000    : {cp1000:.1f}%")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
