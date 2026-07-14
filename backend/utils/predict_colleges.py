"""
predict_colleges.py  —  end-user college recommender

predict_colleges(marks, community, top_n=5)
  1. rank_model_final.pkl  -> predicted rank + ±100 range
  2. cutoff_lookup_2026.csv -> 2026 predicted closing ranks for the community
  3. keep attainable colleges, compute safety margin + status
  4. attach college name/type/district (college_codes.csv, best-effort)
     and branch name (course_codes.csv). 2022+ cutoffs use alpha branch codes
     that map to course_codes.csv (~78% of rows); unmapped codes fall back to
     "Branch <code>".
  5. rank by college tier then branch competitiveness, return top_n
"""

import numpy as np
import pandas as pd
from pathlib import Path

try:
    from .ml_utils import predict_rank          # as package: backend.utils
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from ml_utils import predict_rank           # as flat script

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"

# ── closing_rank -> closing_mark inversion  (HISTORICAL 2022-2025 ONLY) ─────────
# Deliberately independent of rank_model_final.pkl (now 2026-primary) and of the
# 2026 CDF. Built straight from ranks.csv, restricted to 2022/2024/2025 and
# EXCLUDING both 2023 (mark-collapse anomaly) and 2026 (kept out of this feature
# by contract). Percentile-based, per community, same recency weighting the rank
# model used before the 2026 retrain (2023's weight dropped).
INV_YEARS = [2022, 2024, 2025]           # 2023 excluded (anomaly); 2026 excluded (by contract)
INV_WEIGHTS = {2022: 0.10, 2024: 0.25, 2025: 0.60}
_INV = {}   # community -> {"marks": np.array asc, "norms": np.array}, plus "_T", "_years"


def _build_closing_mark_index():
    """Per-community percentile<->mark curve from 2022/2024/2025 overall ranks."""
    df = pd.read_csv(DATA_DIR / "ranks.csv",
                     usecols=["rank", "aggregate_mark", "community", "year"])
    df = df[df["year"].isin(INV_YEARS)].copy()          # hard-exclude 2023 + 2026
    df["community"] = df["community"].replace("BCM", "BC")
    df["mr"] = (df["aggregate_mark"] * 2).round() / 2

    totals = {y: int((df["year"] == y).sum()) for y in INV_YEARS}
    wsum = sum(INV_WEIGHTS[y] for y in INV_YEARS)
    T = sum(INV_WEIGHTS[y] * totals[y] for y in INV_YEARS) / wsum   # weighted cohort size

    _INV["_T"] = T
    _INV["_years"] = list(INV_YEARS)
    _INV["_totals"] = totals

    for comm in sorted(df["community"].unique()):
        # weighted mean normalized-rank (overall_rank / cohort) per rounded mark
        acc = {}   # mark -> [weighted_norm_sum, weight_sum]
        for y in INV_YEARS:
            sub = df[(df["year"] == y) & (df["community"] == comm)]
            if sub.empty:
                continue
            norm_by_mark = sub.groupby("mr")["rank"].mean() / totals[y]
            w = INV_WEIGHTS[y]
            for mark, nr in norm_by_mark.items():
                a = acc.setdefault(mark, [0.0, 0.0])
                a[0] += w * nr
                a[1] += w
        if not acc:
            continue
        marks = np.array(sorted(acc), dtype=float)
        norms = np.array([acc[m][0] / acc[m][1] for m in marks], dtype=float)
        # enforce monotone (norm decreases as mark increases) for a stable inverse
        norms = np.minimum.accumulate(norms)
        _INV[comm] = {"marks": marks, "norms": norms}
    return _INV


def _inv():
    if not _INV:
        _build_closing_mark_index()
    return _INV


def _hist_forward_norm(mark, community):
    """mark -> normalized rank, using the same 2022-2025 per-community curve."""
    idx = _inv()
    community = "BC" if community == "BCM" else community
    c = idx.get(community)
    if c is None:
        return None
    # marks ascending; norms descending -> np.interp needs increasing xp (marks)
    return float(np.interp(mark, c["marks"], c["norms"]))


def _closing_mark(closing_rank, community):
    """closing_rank (overall) + community -> closing_mark, from 2022-2025 only."""
    idx = _inv()
    community = "BC" if community == "BCM" else community
    c = idx.get(community)
    if c is None or closing_rank is None or closing_rank <= 0:
        return None
    norm_q = closing_rank / idx["_T"]
    marks, norms = c["marks"], c["norms"]
    # invert: given norm, recover mark. norms are descending in mark, so sort by
    # norm ascending to satisfy np.interp's increasing-xp requirement.
    order = np.argsort(norms)
    xp, fp = norms[order], marks[order]
    norm_q = float(np.clip(norm_q, xp[0], xp[-1]))
    return round(float(np.interp(norm_q, xp, fp)), 2)

# college_type -> tier rank (lower = more prestigious / preferred)
TIER_RANK = {
    "University Departments": 0,
    "Constituent Colleges": 1,
    "Government Colleges": 2,
    "Government Aided Colleges": 3,
    "Cecri And Cipet": 4,
    "Self Financing Engineering Colleges": 5,
}
SAFE_MARGIN = 500  # margin above which a seat is "SAFE"

_CACHE = {}


def _load():
    if not _CACHE:
        lk = pd.read_csv(DATA_DIR / "cutoff_lookup_2026.csv")
        lk["community"] = lk["community"].replace("BCM", "BC")
        cc = pd.read_csv(DATA_DIR / "college_codes.csv")
        cr = pd.read_csv(DATA_DIR / "course_codes.csv")
        _CACHE["lookup"] = lk
        _CACHE["colleges"] = cc.set_index("college_code").to_dict("index")
        _CACHE["branches"] = dict(
            zip(cr["branch_code"].astype(str), cr["branch_name"]))
    return _CACHE["lookup"], _CACHE["colleges"], _CACHE["branches"]


def _status(margin):
    if margin < 0:
        return "WONT_GET"
    if margin <= SAFE_MARGIN:
        return "MARGINAL"
    return "SAFE"


def _confidence_from_ratio(ratio):
    """Pure RANK curve (fallback when marks/inversion unavailable).
    ratio <= 1: 95 -> 80.  ratio > 1: 80/ratio.  Continuous at 1. Floor 5."""
    if ratio <= 1.0:
        prob = 95 - (15 * ratio)
    else:
        prob = 80 / ratio
    return int(max(5, min(95, prob)))


# far-reach formula value exactly at the near-miss/far boundary (rank_ratio=1.5).
# 80/1.5 = 53.33 — band 2's bottom is anchored to THIS (not a round 50) so there
# is no jump into band 3.
_FAR_AT_1P5 = 80.0 / 1.5


def _hybrid_confidence(rank_ratio, mark_ratio):
    """rank_ratio selects the band; mark_ratio (2022-2025 inversion) nudges.

    1) SAFE     (rank_ratio <= 1):   80 + 15*(1 - clamp(mark_ratio,0,1))  -> [80,95]
    2) near-miss (1 < rank_ratio<=1.5): linear base 80 -> 53.33 on rank_ratio,
       plus a small mark nudge (+/-8) windowed to vanish at both ends.
    3) far reach (rank_ratio > 1.5):  pure rank 80/rank_ratio (no mark influence).

    Continuous at rank_ratio=1.5 by construction (window=0, base=53.33=80/1.5).
    Continuous at rank_ratio=1 when mark_ratio~1 (the usual case at a cutoff);
    a residual step there only appears if rank and mark signals disagree.
    """
    if rank_ratio <= 1.0:
        nmr = min(1.0, max(0.0, mark_ratio))
        prob = 80 + 15 * (1 - nmr)
    elif rank_ratio <= 1.5:
        base = 80 + (_FAR_AT_1P5 - 80) * (rank_ratio - 1.0) / 0.5   # 80 -> 53.33
        window = 16 * (rank_ratio - 1.0) * (1.5 - rank_ratio)       # 0 at ends, 1 at mid
        nudge = max(-8.0, min(8.0, 15 * (1 - mark_ratio))) * window
        prob = base + nudge
    else:
        prob = 80 / rank_ratio
    return int(max(5, min(95, prob)))


def _match_confidence(rank_conf, status, safety_margin=0, closing_rank=1,
                      student_mark=None, community=None):
    # HYBRID: rank_ratio picks the band, mark_ratio (2022-2025 inversion) nudges.
    if closing_rank and closing_rank > 0:
        rank_ratio = (closing_rank - safety_margin) / closing_rank
        if student_mark and student_mark > 0 and community is not None:
            closing_mark = _closing_mark(closing_rank, community)
            if closing_mark is not None:
                return _hybrid_confidence(rank_ratio, closing_mark / student_mark)
        # marks/inversion unavailable -> pure rank curve
        return _confidence_from_ratio(rank_ratio)

    # closing_rank unknown/invalid
    return rank_conf


def predict_colleges(marks, community, top_n=5, forced_rank=None):
    if community == "BCM":
        community = "BC"
    lookup, colleges, branches = _load()

    # Pre-compute all community closing ranks per college+branch combo
    comm_rank_map = {}
    for _, row in lookup.iterrows():
        key = (int(row['college_code']), str(row['branch_code']))
        comm_rank_map.setdefault(key, {})[str(row['community'])] = int(row['predicted_closing_rank_2026'])

    if forced_rank is not None:
        pred_rank = forced_rank
        rmin = rmax = forced_rank
        rank_conf = 100
    else:
        rk = predict_rank(marks, community)
        if "error" in rk:
            return rk
        pred_rank = int(rk["predicted_rank"])
        rmin, rmax = int(rk["range_min"]), int(rk["range_max"])
        rank_conf = int(rk["confidence"])

    df = lookup[lookup["community"] == community].copy()
    # attainable: predicted closing rank is at/after the student's rank
    # (margin >= 0). Uses predicted_rank, not range_min, so WONT_GET combos
    # are excluded from recommendations.
    df = df[df["predicted_closing_rank_2026"] >= pred_rank]
    df["safety_margin"] = df["predicted_closing_rank_2026"] - pred_rank
    df["status"] = df["safety_margin"].apply(_status)

    def tier_of(code):
        info = colleges.get(code)
        return TIER_RANK.get(info["college_type"], 9) if info else 9

    df["tier"] = df["college_code"].apply(tier_of)
    # most prestigious college + most competitive (lowest closing) branch first
    df = df.sort_values(["tier", "predicted_closing_rank_2026"]).head(top_n)

    recs = []
    for i, (_, row) in enumerate(df.iterrows(), 1):
        code = int(row["college_code"])
        info = colleges.get(code)
        bcode = str(row["branch_code"])
        margin = int(row["safety_margin"])
        status = row["status"]
        recs.append({
            "rank": i,
            "college_code": code,
            "college_name": info["college_name_full"] if info else f"College {code}",
            "college_type": info["college_type"] if info else "Unknown",
            "college_district": info["district"] if info else "Unknown",
            "branch_code": bcode,
            "branch_name": branches.get(bcode, f"Branch {bcode}"),
            "closing_rank": int(row["predicted_closing_rank_2026"]),
            "safety_margin": margin,
            "status": status,
            "match_confidence": int(_match_confidence(rank_conf, status, margin, int(row["predicted_closing_rank_2026"]),
                                                       student_mark=marks, community=community)),
            "community_closing_ranks": comm_rank_map.get((code, str(row["branch_code"])), {}),
        })

    return {
        "student_rank": pred_rank,
        "student_rank_range": [rmin, rmax],
        "rank_confidence": rank_conf,
        "community": community,
        "recommendations": recs,
        "verified_rank": forced_rank is not None,
    }


if __name__ == "__main__":
    import json
    for m, c in [(200, "OC"), (195, "BC"), (150, "SC"), (100, "MBC"), (75, "SCA")]:
        print("=" * 60)
        print(f"marks={m} community={c}")
        print(json.dumps(predict_colleges(m, c), indent=2))
