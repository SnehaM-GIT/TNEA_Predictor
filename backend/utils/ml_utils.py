"""
ml_utils_hybrid.py

Hybrid TNEA rank prediction utility.

Load the trained hybrid model and make predictions:
    pred = predict_rank_hybrid(aggregate_mark=195, community="OC")
    
Returns:
    {
        "rank": 850,
        "rank_min": 800,
        "rank_max": 900,
        "confidence": 95,
        "components": {...}
    }
"""

import pickle
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "cleaned"

# ── Load model ───────────────────────────────────────────────────────────────
MODEL_DATA = None

def load_model():
    global MODEL_DATA
    if MODEL_DATA is None:
        with open(DATA_DIR / "rank_model_hybrid.pkl", "rb") as f:
            MODEL_DATA = pickle.load(f)
    return MODEL_DATA

def predict_rank_hybrid(aggregate_mark, community):
    """
    Predict TNEA rank using hybrid statistical model.
    
    Args:
        aggregate_mark : float (0-200)
        community      : str (OC, BC, SC, ST, MBC, SCA, BCM)
    
    Returns:
        {
            "rank": int,           # Most likely rank
            "rank_min": int,       # Lower bound of confidence range
            "rank_max": int,       # Upper bound of confidence range  
            "confidence": int,     # Confidence score (0-100)
            "components": {        # Breakdown of prediction
                "mark_pred": float,
                "community_multiplier": float,
                "trend": str,
                ...
            }
        }
    """
    
    model = load_model()
    
    mark_analysis = model["mark_analysis"]
    community_analysis = model["community_analysis"]
    interpolators = model["interpolators"]
    trend_model = model["trend_model"]
    
    # Normalize community
    if community == "BCM":
        community = "BC"
    
    components = {}
    
    # ── Component 1: Mark-based prediction ─────────────────────────────────
    mark_rounded = round(aggregate_mark * 2) / 2
    
    if mark_rounded in mark_analysis:
        mark_pred = mark_analysis[mark_rounded]["avg_rank"]
        mark_std = mark_analysis[mark_rounded]["std_rank"]
        mark_samples = mark_analysis[mark_rounded]["total"]
        mark_confidence = min(mark_samples / 50, 1.0)
        components["mark_pred"] = f"{mark_pred:.0f}"
        components["mark_samples"] = mark_samples
    else:
        # Try interpolation
        if community in interpolators:
            try:
                mark_pred = float(interpolators[community](aggregate_mark))
                mark_std = 500
                mark_confidence = 0.5
                components["method"] = "interpolated"
                components["mark_pred"] = f"{mark_pred:.0f}"
            except:
                return {
                    "error": f"No data available for mark={aggregate_mark}, community={community}"
                }
        else:
            return {
                "error": f"Community {community} not in training data"
            }
    
    # ── Component 2: Community adjustment ──────────────────────────────────
    if community in community_analysis:
        comm_multiplier = community_analysis[community]["multiplier"]
        comm_avg = community_analysis[community]["avg_rank"]
        components["community_avg_rank"] = f"{comm_avg:.0f}"
        components["community_multiplier"] = f"{comm_multiplier:.3f}"
        community_adjusted = mark_pred * comm_multiplier
    else:
        community_adjusted = mark_pred
        components["community"] = "not_in_training"
    
    # ── Component 3: Trend adjustment ──────────────────────────────────────
    trend_adjustment = 1.0
    if community in trend_model:
        trend_info = trend_model[community]
        components["trend"] = trend_info["trend"]
        
        if trend_info["trend"] == "improving":
            trend_adjustment = 0.98
        elif trend_info["trend"] == "worsening":
            trend_adjustment = 1.02
        
        components["trend_adjustment"] = f"{trend_adjustment:.3f}"
    
    # ── Final prediction ───────────────────────────────────────────────────
    final_pred = community_adjusted * trend_adjustment
    final_pred = max(1, int(final_pred))
    
    # ── Confidence interval ────────────────────────────────────────────────
    # Use historical std dev
    confidence_interval = max(50, min(200, mark_std * (1 - mark_confidence)))
    
    rank_min = max(1, int(final_pred - confidence_interval / 2))
    rank_max = int(final_pred + confidence_interval / 2)
    
    confidence_pct = int(mark_confidence * 100)
    
    # ── Historical cases ───────────────────────────────────────────────────
    historical_cases = []
    
    # Find similar marks in training data
    if mark_rounded in mark_analysis:
        year_dist = mark_analysis[mark_rounded]["year_dist"]
        for year, stats in year_dist.items():
            if isinstance(stats, dict) and "count" in stats:
                historical_cases.append(
                    f"{year}: {stats['count']} students with marks≈{mark_rounded}"
                )
    
    return {
        "mark": aggregate_mark,
        "community": community,
        "rank": final_pred,
        "rank_min": rank_min,
        "rank_max": rank_max,
        "confidence": confidence_pct,
        "components": components,
        "historical_cases": historical_cases,
    }

def predict_batch(students_list):
    """
    Predict ranks for multiple students.
    
    Args:
        students_list: [{"mark": X, "community": Y}, ...]
    
    Returns:
        List of predictions
    """
    return [
        predict_rank_hybrid(s["mark"], s["community"])
        for s in students_list
    ]

# ── Self-test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading model …")
    load_model()
    print("✅ Model loaded")
    
    print("\nTest predictions:")
    test_cases = [
        {"mark": 200, "community": "OC"},
        {"mark": 198, "community": "MBC"},
        {"mark": 150, "community": "BC"},
        {"mark": 100, "community": "SC"},
    ]
    
    for case in test_cases:
        pred = predict_rank_hybrid(case["mark"], case["community"])
        if "error" not in pred:
            print(f"\nMark={case['mark']}, Community={case['community']}")
            print(f"  Predicted Rank: {pred['rank']:,}")
            print(f"  Range: {pred['rank_min']:,} – {pred['rank_max']:,}")
            print(f"  Confidence: {pred['confidence']}%")
        else:
            print(f"\n❌ {case}: {pred['error']}")