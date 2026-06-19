from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, PasswordResetToken
import bcrypt
import jwt
import os
import secrets
import resend
import traceback
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set")

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

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1.0"/></head>
<body style="margin:0;padding:0;background:#0f0f13;font-family:Inter,Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0f0f13;padding:40px 16px;">
    <tr><td align="center">
      <table width="560" cellpadding="0" cellspacing="0"
             style="background:#1a1a24;border-radius:16px;overflow:hidden;border:1px solid #2a2a3a;max-width:560px;width:100%;">

        <!-- Header -->
        <tr>
          <td style="background:linear-gradient(135deg,#8b7355,#a0845c);padding:32px 40px;text-align:center;">
            <div style="font-size:36px;margin-bottom:8px;">🎓</div>
            <h1 style="margin:0;color:#fff;font-size:24px;font-weight:800;letter-spacing:-0.5px;">PickMySeat</h1>
            <p style="margin:6px 0 0;color:rgba(255,255,255,0.8);font-size:13px;">AI-powered TNEA College Seat Predictor</p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px;">
            <h2 style="margin:0 0 12px;color:#f0ece6;font-size:20px;font-weight:700;">🔑 Reset Your Password</h2>
            <p style="margin:0 0 24px;color:#a0a0b0;font-size:15px;line-height:1.6;">
              We received a request to reset the password for your PickMySeat account.
              Click the button below — this link is valid for <strong style="color:#c9a87a;">1 hour</strong>.
            </p>

            <!-- CTA Button -->
            <table cellpadding="0" cellspacing="0" style="margin:0 auto 32px;">
              <tr>
                <td align="center" style="border-radius:10px;background:linear-gradient(135deg,#8b7355,#a0845c);">
                  <a href="{reset_url}"
                     style="display:inline-block;padding:14px 40px;color:#fff;font-size:16px;
                            font-weight:700;text-decoration:none;border-radius:10px;
                            background:linear-gradient(135deg,#8b7355,#a0845c);">
                    Reset My Password →
                  </a>
                </td>
              </tr>
            </table>

            <!-- Fallback URL -->
            <p style="margin:0 0 6px;color:#606070;font-size:13px;">Button not working? Copy this link:</p>
            <p style="margin:0 0 28px;word-break:break-all;">
              <a href="{reset_url}" style="color:#c9a87a;font-size:12px;text-decoration:none;">{reset_url}</a>
            </p>

            <!-- Security note -->
            <div style="background:#13131c;border-left:3px solid #8b7355;border-radius:6px;padding:14px 16px;margin-bottom:24px;">
              <p style="margin:0;color:#a0a0b0;font-size:13px;line-height:1.5;">
                ⚠️ If you didn't request a password reset, you can safely ignore this email.
                Your account has not been changed.
              </p>
            </div>

            <p style="margin:0;color:#505060;font-size:13px;">— The PickMySeat Team</p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="background:#13131c;padding:18px 40px;text-align:center;border-top:1px solid #2a2a3a;">
            <p style="margin:0 0 4px;color:#404050;font-size:12px;">
              PickMySeat · TNEA 2026 College Predictor · pickmyseat.in
            </p>
            <p style="margin:0;font-size:12px;">
              <a href="mailto:support.pickmyseat@gmail.com"
                 style="color:#8b7355;text-decoration:none;">support.pickmyseat@gmail.com</a>
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    resend.api_key = os.getenv("RESEND_API_KEY")
    if not resend.api_key:
        raise RuntimeError("RESEND_API_KEY environment variable is not set")

    print(f"[Resend] sending to {to_email}")
    try:
        response = resend.Emails.send({
            "from": "PickMySeat <support@pickmyseat.in>",
            "reply_to": "support.pickmyseat@gmail.com",
            "to": [to_email],
            "subject": "Reset your PickMySeat password",
            "html": html,
        })
        print(f"[Resend] ok — id={response.get('id') if isinstance(response, dict) else getattr(response, 'id', response)}")
    except Exception as e:
        print(f"[Resend] FAILED: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        raise

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
        category_locked=bool(data.community),   # lock immediately if community provided at signup
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
            "category_locked": user.category_locked,
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
        if user.category_locked and data.community is not None and data.community != '':
            raise HTTPException(status_code=403, detail="Category is locked after first submission")
        if data.name is not None: user.name = data.name
        if data.mobile is not None: user.mobile = data.mobile
        # Only update community when a real (non-empty) value is supplied
        if data.community:
            user.community = data.community
            user.category_locked = True   # lock on first save
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
        return {"status": "profile updated", "marks_locked": user.marks_locked, "category_locked": user.category_locked}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email address not found. Please check and try again.")
        
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
        print(f"[forgot-password] send failed for {user.email}: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send reset email. Please try again later.")

    return {"message": "A reset link has been sent to your email."}

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

@router.get("/recent-users")
def recent_users(db: Session = Depends(get_db)):
    """Return first names + a ticker message for the last 10 registered users.
    This is a public, low-sensitivity endpoint — it only exposes first names.
    """
    import random
    users = (
        db.query(User)
        .order_by(User.id.desc())
        .limit(10)
        .all()
    )
    action_templates = [
        "{name} just joined PickMySeat 🎉",
        "{name} predicted their college seat 🎯",
        "{name} is exploring TNEA colleges 🏛️",
        "{name} checked their rank prediction 🏆",
        "{name} unlocked 15 college combinations 🚀",
    ]
    result = []
    for u in users:
        first_name = (u.name or "A student").split()[0]
        action = random.choice(action_templates).format(name=first_name)
        result.append({"first_name": first_name, "action": action})
    return result