from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from ml_service import get_rank_prediction, get_college_predictions_filtered

router = APIRouter()

class MarksInput(BaseModel):
    maths: float
    physics: float
    chemistry: float
    community: str
    top_n: int = 5
    preferred_colleges: Optional[List[int]] = None   # list of college codes
    preferred_branches: Optional[List[str]] = None   # list of branch codes

@router.post("/rank")
def predict_rank(data: MarksInput):
    marks = data.maths + data.physics / 2 + data.chemistry / 2
    try:
        return get_rank_prediction(marks, data.community)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/colleges")
def predict_colleges(data: MarksInput):
    marks = data.maths + data.physics / 2 + data.chemistry / 2
    try:
        return get_college_predictions_filtered(
            marks=marks,
            community=data.community,
            top_n=data.top_n,
            preferred_colleges=data.preferred_colleges,
            preferred_branches=data.preferred_branches
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))