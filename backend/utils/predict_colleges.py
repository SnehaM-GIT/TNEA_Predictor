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


def _match_confidence(rank_conf, status):
    if status == "SAFE":
        return min(95, rank_conf + 10)
    if status == "MARGINAL":
        return rank_conf
    return max(10, rank_conf - 30)


def predict_colleges(marks, community, top_n=5):
    if community == "BCM":
        community = "BC"
    lookup, colleges, branches = _load()

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
            "match_confidence": int(_match_confidence(rank_conf, status)),
        })

    return {
        "student_rank": pred_rank,
        "student_rank_range": [rmin, rmax],
        "rank_confidence": rank_conf,
        "community": community,
        "recommendations": recs,
    }


if __name__ == "__main__":
    import json
    for m, c in [(200, "OC"), (195, "BC"), (150, "SC"), (100, "MBC"), (75, "SCA")]:
        print("=" * 60)
        print(f"marks={m} community={c}")
        print(json.dumps(predict_colleges(m, c), indent=2))
