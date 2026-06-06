from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User
import bcrypt
import jwt
import os
from datetime import datetime, timedelta

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY", "pickmyseat_secret")

class SignupInput(BaseModel):
    email: str
    password: str
    name: str
    mobile: str
    community: str

class LoginInput(BaseModel):
    email: str
    password: str

def create_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/signup")
def signup(data: SignupInput, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()
    user = User(
        email=data.email,
        password_hash=hashed,
        name=data.name,
        mobile=data.mobile,
        community=data.community,
        grade="2"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_token(user.id)
    return {"token": token, "grade": user.grade, "name": user.name}

@router.post("/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    if not bcrypt.checkpw(data.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    
    token = create_token(user.id)
    return {"token": token, "grade": user.grade, "name": user.name}