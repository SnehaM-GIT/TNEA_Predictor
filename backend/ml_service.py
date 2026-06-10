import sys
from pathlib import Path
from typing import Optional, List

sys.path.insert(0, str(Path(__file__).resolve().parent / "utils"))

from predict_colleges import predict_colleges
from ml_utils import predict_rank


def get_rank_prediction(marks: float, community: str):
    result = predict_rank(marks, community)
    if "error" in result:
        raise ValueError(result["error"])
    return result


Vdef get_college_predictions_filtered(
    marks: float,
    community: str,
    top_n: int = 5,
    preferred_colleges: Optional[List[int]] = None,
    preferred_branches: Optional[List[str]] = None
):
    if preferred_colleges or preferred_branches:
        import pandas as pd
        from pathlib import Path
        from utils.predict_colleges import _load, _match_confidence, _status
        from utils.ml_utils import predict_rank

        if community == "BCM":
            community = "BC"

        rk = predict_rank(marks, community)
        if "error" in rk:
            raise ValueError(rk["error"])

        pred_rank  = int(rk["predicted_rank"])
        rank_conf  = int(rk["confidence"])

        lookup, colleges, branches = _load()

        df = lookup[lookup["community"] == community].copy()
        df = df[df["predicted_closing_rank_2026"] >= pred_rank]

        if preferred_colleges:
            df = df[df["college_code"].isin(preferred_colleges)]
        if preferred_branches:
            df = df[df["branch_code"].isin(preferred_branches)]

        df["safety_margin"] = df["predicted_closing_rank_2026"] - pred_rank
        df["status"]        = df["safety_margin"].apply(_status)

        recs = []
        for _, row in df.iterrows():
            code   = int(row["college_code"])
            info   = colleges.get(code)
            bcode  = str(row["branch_code"])
            margin = int(row["safety_margin"])
            status = row["status"]
            closing = int(row["predicted_closing_rank_2026"])
            recs.append({
                "rank":             len(recs) + 1,
                "college_code":     code,
                "college_name":     info["college_name_full"] if info else f"College {code}",
                "college_type":     info["college_type"]      if info else "Unknown",
                "college_district": info["district"]          if info else "Unknown",
                "branch_code":      bcode,
                "branch_name":      branches.get(bcode, f"Branch {bcode}"),
                "closing_rank":     closing,
                "safety_margin":    margin,
                "status":           status,
                "match_confidence": int(_match_confidence(rank_conf, status, margin, closing)),
            })

        recs.sort(key=lambda x: x["match_confidence"], reverse=True)
        recs = recs[:top_n]
        for i, r in enumerate(recs, 1):
            r["rank"] = i

        return {
            "student_rank":       pred_rank,
            "student_rank_range": [int(rk["range_min"]), int(rk["range_max"])],
            "rank_confidence":    rank_conf,
            "community":          community,
            "recommendations":    recs,
            "message":            "No matches found. Try broadening your filters." if not recs else None
        }

    # No preferences — use original predict_colleges
    result = predict_colleges(marks, community, top_n=top_n)
    if "error" in result:
        raise ValueError(result["error"])
    return result