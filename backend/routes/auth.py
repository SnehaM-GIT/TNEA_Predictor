from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, PasswordResetToken
import bcrypt
import jwt
import os
import secrets
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Optional

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

class UpdateProfileInput(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    community: Optional[str] = None
    maths: Optional[float] = None
    physics: Optional[float] = None
    chemistry: Optional[float] = None
    preferred_colleges: Optional[str] = None
    preferred_courses: Optional[str] = None
    application_id: Optional[str] = None

class ForgotPasswordInput(BaseModel):
    email: str

class ValidateTokenInput(BaseModel):
    token: str

class ResetPasswordInput(BaseModel):
    token: str
    new_password: str

def create_token(user_id: int):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=30)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def send_reset_email(to_email: str, token: str):
    reset_url = f"{os.getenv('RESET_BASE_URL', 'https://pickmyseat.in')}/reset-password.html?token={token}"
    body = f"""Hi,

You requested a password reset for your PickMySeat account.

Click the link below to reset your password (valid for 1 hour):
{reset_url}

If you didn't request this, ignore this email.

— PickMySeat Team
"""
    msg = MIMEText(body)
    msg['Subject'] = 'Reset your PickMySeat password'
    msg['From']    = os.getenv('SMTP_USER')
    msg['To']      = to_email

    with smtplib.SMTP(os.getenv('SMTP_HOST', 'smtp.gmail.com'), int(os.getenv('SMTP_PORT', 587))) as server:
        server.starttls()
        server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASS'))
        server.send_message(msg)

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

@router.get("/me")
def get_me(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = db.query(User).filter(User.id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "community": user.community,
            "grade": user.grade,
            "has_paid": user.has_paid,
            "marks_locked": user.marks_locked,
            "maths": user.maths,
            "physics": user.physics,
            "chemistry": user.chemistry,
            "aggregate": user.aggregate,
            "rank": user.rank,
            "preferred_colleges": user.preferred_colleges,
            "preferred_courses": user.preferred_courses,
            "application_id": user.application_id,
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/update-profile")
def update_profile(
    data: UpdateProfileInput,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = db.query(User).filter(User.id == payload.get("user_id")).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if user.marks_locked and (data.maths is not None or data.physics is not None or data.chemistry is not None):
            raise HTTPException(status_code=403, detail="Marks are locked after payment")
        if data.name is not None: user.name = data.name
        if data.mobile is not None: user.mobile = data.mobile
        if data.community is not None: user.community = data.community
        if data.maths is not None: user.maths = data.maths
        if data.physics is not None: user.physics = data.physics
        if data.chemistry is not None: user.chemistry = data.chemistry
        if data.maths and data.physics and data.chemistry:
            user.aggregate = data.maths + data.physics / 2 + data.chemistry / 2
            user.marks_locked = True
        if data.preferred_colleges is not None: user.preferred_colleges = data.preferred_colleges
        if data.preferred_courses is not None: user.preferred_courses = data.preferred_courses
        if data.application_id is not None: user.application_id = data.application_id
        db.commit()
        return {"status": "profile updated", "marks_locked": user.marks_locked}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if user:
        # delete any existing unused tokens for this user
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used == False
        ).delete()
        db.commit()

        token = secrets.token_urlsafe(32)
        db.add(PasswordResetToken(
            user_id    = user.id,
            token      = token,
            expires_at = datetime.utcnow() + timedelta(hours=1),
            used       = False
        ))
        db.commit()

        try:
            send_reset_email(user.email, token)
        except Exception as e:
            print(f"Email send failed: {e}")

    # always return 200 — don't reveal if email exists
    return {"message": "If that email is registered, a reset link has been sent."}

@router.post("/validate-reset-token")
def validate_reset_token(data: ValidateTokenInput, db: Session = Depends(get_db)):
    row = db.query(PasswordResetToken).filter(
        PasswordResetToken.token      == data.token,
        PasswordResetToken.used       == False,
        PasswordResetToken.expires_at >  datetime.utcnow()
    ).first()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")
    return {"valid": True}

@router.post("/reset-password")
def reset_password(data: ResetPasswordInput, db: Session = Depends(get_db)):
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    row = db.query(PasswordResetToken).filter(
        PasswordResetToken.token      == data.token,
        PasswordResetToken.used       == False,
        PasswordResetToken.expires_at >  datetime.utcnow()
    ).first()
    if not row:
        raise HTTPException(status_code=400, detail="Invalid or expired reset link.")

    user = db.query(User).filter(User.id == row.user_id).first()
    user.password_hash = bcrypt.hashpw(data.new_password.encode(), bcrypt.gensalt()).decode()
    row.used = True
    db.commit()

    return {"message": "Password updated successfully."}