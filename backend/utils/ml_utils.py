"""
Rank prediction with two-tier approach:

PRIMARY (MAE ~589): 2025 mark CDF lookup
  HSC marks published before TNEA ranks => marks are known input features.
  pred_rank = count(students with higher mark) + 1
  Remaining error ~589 is purely from mark-tie aliasing.

FALLBACK (MAE ~3096): historical norm_rank + hybrid shift correction
  Used when current-year mark CDF is unavailable (future-year prediction).
  Hybrid delta = max(community-specific delta, overall delta) to handle
  communities like OC where own marks barely shift but the pool inflates.
"""

import pickle
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"

MODEL_DATA = None


def load_model():
    global MODEL_DATA
    if MODEL_DATA is None:
        with open(DATA_DIR / "rank_model_final.pkl", "rb") as f:
            MODEL_DATA = pickle.load(f)
    return MODEL_DATA


def predict_rank(marks, community, use_cdf=True):
    """
    Production rank prediction with ±range band (Task 1 format).

    Args:
        marks: aggregate mark 0-200
        community: OC, BC, SC, ST, MBC, SCA, BCM

    Returns:
        {
          "predicted_rank": int,
          "range_min": int,   # rank - 100 (clamped >= 1)
          "range_max": int,   # rank + 100
          "confidence": int,  # %
          "basis": str,
        }
        or {"error": ...}
    """
    base = predict_rank_adjusted(marks, community, use_cdf=use_cdf)
    if "error" in base:
        return base

    model = load_model()
    half = model.get("range_halfwidth", 100)
    rank = int(base["rank"])
    return {
        "predicted_rank": rank,
        "range_min": int(max(1, rank - half)),
        "range_max": int(rank + half),
        "confidence": int(base["confidence"]),
        "basis": model.get("basis_label", "percentile-based from 2022-2026 data"),
    }


def predict_rank_adjusted(aggregate_mark, community, use_cdf=True):
    """
    Predict overall TNEA rank for a given mark and community.

    Args:
        aggregate_mark: 0-200
        community: OC, BC, SC, ST, MBC, SCA, BCM
        use_cdf: True = use 2026 mark CDF (MAE ~585, default)
                 False = use historical model with hybrid delta (MAE ~3977)

    Returns:
        dict with rank, confidence, basis  OR  dict with 'error' key
    """
    model = load_model()

    if community == "BCM":
        community = "BC"

    if community not in model["communities"]:
        return {"error": f"Community {community} not in model"}

    # primary_year keys are the current schema; *_2025 names are legacy aliases
    total_students = (model.get("total_students_primary")
                      or model.get("total_students_2025", 239299))
    primary_year = model.get("primary_year", 2025)
    mark_rounded = round(aggregate_mark * 2) / 2

    # ── PRIMARY: current-year mark CDF ────────────────────────────────────────
    cdf = model.get("mark_count_above_primary") or model.get("mark_count_above_2025")
    if use_cdf and cdf is not None:
        if mark_rounded in cdf:
            pred_rank = max(1, cdf[mark_rounded] + 1)
            norm_rank = pred_rank / total_students
            confidence = min(90, max(30, int((1 - abs(norm_rank - 0.5)) * 100)))
            return {
                "mark": aggregate_mark,
                "community": community,
                "rank": pred_rank,
                "confidence": confidence,
                "norm_rank": round(norm_rank, 4),
                "delta_applied": 0.0,
                "delta_source": f"cdf_{primary_year}",
                "basis": "cdf_exact",
            }
        # Mark outside CDF range — fall through to historical model

    # ── FALLBACK: historical norm_rank + hybrid shift correction ──────────────
    overall_norm_rank = model["overall_norm_rank"]
    overall_interp = model["overall_interp"]

    delta = model.get("hybrid_actual_delta", {}).get(
        community,
        (model.get("comm_actual_delta")
         or model.get("comm_actual_delta_2025", {})).get(community, 0.0)
    )
    delta_source = "hybrid_actual"

    adj_mark = aggregate_mark - delta
    adj_rounded = round(adj_mark * 2) / 2

    if adj_rounded in overall_norm_rank:
        norm_rank = overall_norm_rank[adj_rounded]
        basis = "hist_exact"
    else:
        norm_rank = float(overall_interp(adj_mark))
        norm_rank = float(np.clip(norm_rank, 0.0001, 1.0))
        basis = "hist_interp"

    pred_rank = max(1, int(norm_rank * total_students))
    confidence = min(85, max(15, int((1 - abs(norm_rank - 0.5)) * 100)))

    return {
        "mark": aggregate_mark,
        "community": community,
        "rank": pred_rank,
        "confidence": confidence,
        "norm_rank": round(norm_rank, 4),
        "delta_applied": round(delta, 2),
        "delta_source": delta_source,
        "basis": basis,
    }


if __name__ == "__main__":
    print("Loading model ...")
    m = load_model()
    print(f"Model type: {m.get('type')}")
    print(f"Val MAE (CDF): {m.get('val_mae_cdf', 'N/A')}")
    print(f"Val MAE (hybrid fallback): {m.get('val_mae_hybrid_actual', 'N/A')}\n")

    test_cases = [
        {"mark": 200, "community": "OC"},
        {"mark": 198, "community": "MBC"},
        {"mark": 180, "community": "BC"},
        {"mark": 150, "community": "SC"},
        {"mark": 120, "community": "ST"},
    ]

    for case in test_cases:
        pred = predict_rank_adjusted(case["mark"], case["community"])
        if "error" not in pred:
            print(f"Mark {case['mark']}, {case['community']}: "
                  f"rank {pred['rank']:,}  "
                  f"(norm={pred['norm_rank']}, basis={pred['basis']}, "
                  f"confidence={pred['confidence']}%)")
        else:
            print(f"ERROR {case}: {pred['error']}")
