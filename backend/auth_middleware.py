import os
import jwt
from fastapi import HTTPException, Header
from typing import Optional
from sqlalchemy.orm import Session
from models import User

SECRET_KEY = os.getenv("SECRET_KEY")

def get_current_user(authorization: Optional[str] = Header(None), db: Session = None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def require_grade(user: User, min_grade: str):
    grade_order = {"3": 0, "2": 1, "1": 2}
    if grade_order.get(user.grade, 0) < grade_order.get(min_grade, 0):
        raise HTTPException(
            status_code=403,
            detail=f"This feature requires Grade {min_grade} or higher"
        )