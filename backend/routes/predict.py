from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, validator
from typing import Optional, List
from sqlalchemy.orm import Session
from database import get_db
from ml_service import get_rank_prediction, get_college_predictions_filtered
from auth_middleware import get_current_user, require_grade
from models import User, Prediction, RankInput
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime
import pandas as pd
from pathlib import Path
import jwt, os

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

VALID_COMMUNITIES = {"OC", "BC", "BCM", "MBC", "SC", "ST", "SCA"}
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "cleaned"

class MarksInput(BaseModel):
    maths: float
    physics: float
    chemistry: float
    community: str
    top_n: int = 5
    preferred_colleges: Optional[List[int]] = None
    preferred_branches: Optional[List[str]] = None

    @validator('maths', 'physics', 'chemistry')
    def clamp_marks(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Marks must be between 0 and 100')
        return round(v, 2)

    @validator('community')
    def validate_community(cls, v):
        if v.upper() not in VALID_COMMUNITIES:
            raise ValueError(f'Community must be one of {VALID_COMMUNITIES}')
        return v.upper()

    @validator('top_n')
    def clamp_top_n(cls, v):
        return max(1, min(v, 20))


class RankInputData(BaseModel):
    actual_rank: int
    aggregate: float
    community: str


def _get_optional_user(authorization: Optional[str], db: Session):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        SECRET_KEY = os.getenv("SECRET_KEY", "pickmyseat_secret")
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return db.query(User).filter(User.id == payload.get("user_id")).first()
    except:
        return None


@router.post("/rank")
@limiter.limit("50/day")
def predict_rank(request: Request, data: MarksInput):
    marks = data.maths + data.physics / 2 + data.chemistry / 2
    try:
        return get_rank_prediction(marks, data.community)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/colleges")
@limiter.limit("30/day")
def predict_colleges(
    request: Request,
    data: MarksInput,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    marks = data.maths + data.physics / 2 + data.chemistry / 2
    try:
        result = get_college_predictions_filtered(
            marks=marks,
            community=data.community,
            top_n=data.top_n,
            preferred_colleges=data.preferred_colleges,
            preferred_branches=data.preferred_branches
        )

        user = _get_optional_user(authorization, db)
        if user and result.get("recommendations"):
            for rec in result["recommendations"]:
                prediction = Prediction(
                    user_id=user.id,
                    maths=data.maths,
                    physics=data.physics,
                    chemistry=data.chemistry,
                    aggregate=marks,
                    community=data.community,
                    predicted_rank_low=result.get("student_rank_range", [None])[0],
                    predicted_rank_high=result.get("student_rank_range", [None, None])[1],
                    college_code=str(rec["college_code"]),
                    branch_code=rec["branch_code"],
                    probability=rec["match_confidence"]
                )
                db.add(prediction)
            db.commit()

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/combo")
@limiter.limit("10/day")
def predict_combo(
    request: Request,
    data: MarksInput,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_optional_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    require_grade(user, "2")

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


@router.post("/submit-rank")
def submit_rank(
    data: RankInputData,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_optional_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    require_grade(user, "1")

    rank_input = RankInput(
        user_id=user.id,
        actual_rank=data.actual_rank,
        aggregate=data.aggregate,
        community=data.community,
        year=datetime.utcnow().year
    )
    db.add(rank_input)
    user.rank = data.actual_rank
    db.commit()

    return {"status": "rank saved", "rank": data.actual_rank}


@router.get("/colleges-list")
def get_colleges_list():
    df = pd.read_csv(DATA_DIR / "college_codes.csv")
    df = df.fillna("")
    return df[["college_code", "college_name_full", "college_type", "district"]].to_dict(orient="records")


@router.get("/branches-list")
def get_branches_list():
    df = pd.read_csv(DATA_DIR / "course_codes.csv")
    df = df.fillna("")
    return df[["branch_code", "branch_name"]].to_dict(orient="records")


@router.get("/college-branches/{college_code}")
def get_college_branches(college_code: int):
    cutoff_df = pd.read_csv(DATA_DIR / "cutoff_lookup_2026.csv").fillna("")
    branches_df = pd.read_csv(DATA_DIR / "course_codes.csv").fillna("")
    branch_map = dict(zip(branches_df["branch_code"], branches_df["branch_name"]))

    college_branches = cutoff_df[
        cutoff_df["college_code"] == college_code
    ]["branch_code"].unique().tolist()

    return [
        {"code": str(b), "name": branch_map.get(str(b), f"Branch {b}")}
        for b in college_branches
        if b != ""
    ]