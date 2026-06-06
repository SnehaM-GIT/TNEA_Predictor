"""
test_end_to_end.py  —  PickMySeat.AI full-system verification

Run: python backend/scripts/test_end_to_end.py
"""

import sys
import io
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BACKEND = Path(__file__).resolve().parent.parent
DATA = BACKEND / "data" / "cleaned"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(BACKEND / "scripts"))

from utils.ml_utils import predict_rank                 # noqa: E402
from utils.predict_colleges import predict_colleges      # noqa: E402
from build_cutoff_model import fit_predict, COMMUNITIES, MIN_YEAR  # noqa: E402

OK, WARN, BAD = "[OK]", "[!]", "[X]"
status = []


def section(t):
    print("\n" + "=" * 70)
    print(t)
    print("=" * 70)


# ── 1. FILE EXISTENCE ─────────────────────────────────────────────────────────
section("1. REQUIRED FILES")
required = [
    "ranks.csv", "cutoffs.csv", "college_codes.csv", "course_codes.csv",
    "rank_model_final.pkl", "cutoff_predictor.pkl",
    "distribution_2024.pkl", "historical_patterns.pkl",
    "cutoff_lookup_2026.csv", "rank_model_meta.pkl", "cutoff_model_meta.pkl",
]
files_ok = True
for f in required:
    exists = (DATA / f).exists()
    files_ok &= exists
    print(f"  {OK if exists else BAD} {f}")
status.append(("All files present", files_ok))


# ── 2. RANK MODEL ─────────────────────────────────────────────────────────────
section("2. RANK MODEL  (±100 ranges)")
rank_cases = [(200, "OC"), (195, "BC"), (150, "SC"), (100, "MBC"), (75, "SCA")]
rank_ok = True
for m, c in rank_cases:
    r = predict_rank(m, c)
    if "error" in r:
        print(f"  {BAD} marks={m} {c}: {r['error']}")
        rank_ok = False
        continue
    band = r["range_max"] - r["range_min"]
    ok = ("predicted_rank" in r and r["range_min"] >= 1 and band <= 200)
    rank_ok &= ok
    print(f"  {OK if ok else BAD} marks={m:>3} {c:<4} -> rank {r['predicted_rank']:>7,} "
          f"[{r['range_min']:>7,} - {r['range_max']:>7,}]  conf {r['confidence']}%")
status.append(("Rank model ±range", rank_ok))


# ── 3. COLLEGE PREDICTION ─────────────────────────────────────────────────────
section("3. COLLEGE PREDICTION  (top 5, human-readable names)")
pred_ok = True
name_resolved = 0
branch_resolved = 0
total_recs = 0
for m, c in rank_cases:
    res = predict_colleges(m, c, top_n=5)
    if "error" in res:
        print(f"  {BAD} marks={m} {c}: {res['error']}")
        pred_ok = False
        continue
    print(f"\n  marks={m} {c}  student_rank={res['student_rank']:,} "
          f"range={res['student_rank_range']} conf={res['rank_confidence']}%")
    if not res["recommendations"]:
        print(f"    {WARN} no recommendations")
    for r in res["recommendations"]:
        total_recs += 1
        if not r["college_name"].startswith("College "):
            name_resolved += 1
        if not r["branch_name"].startswith("Branch "):
            branch_resolved += 1
        print(f"    #{r['rank']} [{r['status']:<8}] {r['college_name'][:48]:<48} | "
              f"{r['branch_name'][:32]:<32} | close {r['closing_rank']:>7,} "
              f"| margin {r['safety_margin']:>7,} | mc {r['match_confidence']}%")
pred_ok &= total_recs > 0
status.append(("predict_colleges returns recs", pred_ok))
if total_recs:
    print(f"\n  College names resolved: {name_resolved}/{total_recs} "
          f"({name_resolved/total_recs*100:.0f}%)")
    print(f"  Branch names resolved : {branch_resolved}/{total_recs} "
          f"({branch_resolved/total_recs*100:.0f}%)")
status.append(("College name lookup", name_resolved / total_recs > 0.5 if total_recs else False))
status.append(("Branch name lookup", branch_resolved / total_recs > 0.5 if total_recs else False))


# ── 4. CUTOFF MODEL VALIDATION (2024 -> 2025) ─────────────────────────────────
section("4. CUTOFF MODEL VALIDATION  (train 2022-2024 -> predict 2025)")
cut = pd.read_csv(DATA / "cutoffs.csv")
cut["community"] = cut["community"].replace("BCM", "BC")
cut = cut[cut["year"] >= MIN_YEAR]
# collapse counselling rounds -> one row per combo-year (final closing = max)
cut = cut.groupby(
    ["college_code", "branch_code", "community", "year"], as_index=False
).agg(closing_rank=("closing_rank", "max"))
grp = cut.groupby(["college_code", "branch_code", "community"])

errs = {c: [] for c in COMMUNITIES}
all_err, comp_err = [], []
for (cc, bc, comm), g in grp:
    by = dict(zip(g["year"].astype(int), g["closing_rank"].astype(float)))
    if 2025 not in by:
        continue
    tr = [y for y in by if y <= 2024]
    if not tr:
        continue
    pred, _ = fit_predict(tr, [by[y] for y in tr], 2025)
    if pred is None:
        continue
    actual = by[2025]
    e = abs(pred - actual)
    all_err.append(e)
    if actual < 10000:                 # competitive (recommendation-relevant)
        comp_err.append(e)
        if comm in errs:
            errs[comm].append(e)

comp_err = np.array(comp_err, float)
all_err = np.array(all_err, float)
print("  Competitive segment (actual 2025 closing_rank < 10000):")
print(f"  {'Comm':<6}{'MAE':>9}{'median':>9}{'n':>7}")
for comm in COMMUNITIES:
    e = np.array(errs[comm], float)
    if len(e):
        print(f"  {comm:<6}{e.mean():>9.0f}{np.median(e):>9.0f}{len(e):>7,}")
comp_mae = comp_err.mean()
within500 = (comp_err <= 500).mean() * 100
within1000 = (comp_err <= 1000).mean() * 100
print(f"  {'-'*31}")
print(f"  Competitive avg MAE : {comp_mae:.0f}")
print(f"  Full-set avg MAE    : {all_err.mean():.0f}  (noisy low-demand tail)")
print(f"  within ±500         : {within500:.1f}%")
print(f"  within ±1000        : {within1000:.1f}%")
verdict = "GOOD" if comp_mae < 1000 else ("ACCEPTABLE" if comp_mae < 2000 else "NEEDS WORK")
print(f"  VERDICT (competitive): {verdict}")
status.append(("Cutoff competitive MAE < 2000", comp_mae < 2000))


# ── 5. FINAL REPORT ───────────────────────────────────────────────────────────
section("5. FINAL STATUS REPORT")
for label, ok in status:
    print(f"  {OK if ok else BAD} {label}")
all_pass = all(ok for _, ok in status)
print("\n  " + ("SYSTEM READY FOR PRODUCTION" if all_pass
                 else "SOME CHECKS FAILED — see above"))
sys.exit(0 if all_pass else 1)
