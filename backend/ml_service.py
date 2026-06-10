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


def get_college_predictions_filtered(
    marks: float,
    community: str,
    top_n: int = 5,
    preferred_colleges: Optional[List[int]] = None,
    preferred_branches: Optional[List[str]] = None
):
    result = predict_colleges(marks, community, top_n=500)  # get enough to cover preferred filters
    if "error" in result:
        raise ValueError(result["error"])

    recs = result["recommendations"]

    # filter by preferred colleges if provided
    if preferred_colleges:
        recs = [r for r in recs if r["college_code"] in preferred_colleges]

    # filter by preferred branches if provided
    if preferred_branches:
        recs = [r for r in recs if r["branch_code"] in preferred_branches]

    # if both filters give no results, return message
    if not recs and (preferred_colleges or preferred_branches):
        result["recommendations"] = []
        result["message"] = "No matches found for your preferred colleges/branches. Try broadening your filters."
    else:
        result["recommendations"] = recs[:top_n]

    return result