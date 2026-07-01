from fastapi import APIRouter, HTTPException, Depends, Header, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, Payment
from auth_middleware import require_grade
from rate_limiter import limiter
from typing import Optional
from datetime import datetime, timedelta
import razorpay
import hmac
import hashlib
import os
import jwt

ORDER_TTL_MINUTES = 15

router = APIRouter()

RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
SECRET_KEY          = os.getenv("SECRET_KEY")

def _get_user(authorization: Optional[str], db: Session):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return db.query(User).filter(User.id == payload.get("user_id")).first()
    except:
        return None

class VerifyPaymentInput(BaseModel):
    razorpay_order_id:   str
    razorpay_payment_id: str
    razorpay_signature:  str

@router.post("/create-order")
def create_order(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    # Guard: ensure Razorpay keys are configured
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Payment service is not configured. Please contact support."
        )

    user = _get_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if user.has_paid:
        raise HTTPException(status_code=400, detail="Already purchased")

    # Return existing pending order if within TTL — avoids duplicate Razorpay API calls and DB rows
    ttl_cutoff = datetime.utcnow() - timedelta(minutes=ORDER_TTL_MINUTES)
    existing = db.query(Payment).filter(
        Payment.user_id == user.id,
        Payment.status == "created",
        Payment.amount == 14900,
        Payment.created_at >= ttl_cutoff
    ).order_by(Payment.created_at.desc()).first()

    if existing:
        return {
            "order_id":   existing.razorpay_order_id,
            "amount":     14900,
            "currency":   "INR",
            "key_id":     RAZORPAY_KEY_ID,
            "user_name":  user.name,
            "user_email": user.email
        }

    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        order  = client.order.create({
            "amount":   14900,
            "currency": "INR",
            "payment_capture": 1
        })
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Could not create payment order. Please try again. ({str(e)})"
        )

    payment = Payment(
        user_id=user.id,
        razorpay_order_id=order["id"],
        amount=14900,
        status="created"
    )
    db.add(payment)
    db.commit()

    return {
        "order_id":   order["id"],
        "amount":     14900,
        "currency":   "INR",
        "key_id":     RAZORPAY_KEY_ID,
        "user_name":  user.name,
        "user_email": user.email
    }

@router.post("/verify")
def verify_payment(
    data: VerifyPaymentInput,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    if not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Payment service is not configured.")

    # Verify HMAC signature
    body     = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    if expected != data.razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # Update payment record
    payment = db.query(Payment).filter(
        Payment.razorpay_order_id == data.razorpay_order_id
    ).first()
    if payment:
        payment.razorpay_payment_id = data.razorpay_payment_id
        payment.status = "paid"

    # Upgrade user to Grade 1 and lock marks
    user.has_paid    = True
    user.grade       = "1"
    user.marks_locked = True
    db.commit()

    return {"status": "payment verified", "grade": "1"}


@router.post("/create-order-marks")
@limiter.limit("10/day")
def create_order_marks(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if not user.has_paid:
        raise HTTPException(status_code=403, detail="Marks update requires Premium access")

    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        raise HTTPException(status_code=503, detail="Payment service not configured")

    # Return existing pending order if within TTL — avoids duplicate Razorpay API calls and DB rows
    ttl_cutoff = datetime.utcnow() - timedelta(minutes=ORDER_TTL_MINUTES)
    existing = db.query(Payment).filter(
        Payment.user_id == user.id,
        Payment.status == "created",
        Payment.amount == 2500,
        Payment.created_at >= ttl_cutoff
    ).order_by(Payment.created_at.desc()).first()

    if existing:
        return {
            "order_id":   existing.razorpay_order_id,
            "amount":     2500,
            "currency":   "INR",
            "key_id":     RAZORPAY_KEY_ID,
            "user_name":  user.name,
            "user_email": user.email
        }

    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        order  = client.order.create({
            "amount":   2500,
            "currency": "INR",
            "payment_capture": 1
        })
    except Exception as e:
        raise HTTPException(status_code=503, detail="Payment service unavailable. Try again later.")

    payment = Payment(
        user_id=user.id,
        razorpay_order_id=order["id"],
        amount=2500,
        status="created"
    )
    db.add(payment)
    db.commit()

    return {
        "order_id":   order["id"],
        "amount":     2500,
        "currency":   "INR",
        "key_id":     RAZORPAY_KEY_ID,
        "user_name":  user.name,
        "user_email": user.email
    }


class VerifyMarksUpdateInput(BaseModel):
    razorpay_order_id:   str
    razorpay_payment_id: str
    razorpay_signature:  str
    maths:   float
    physics: float
    chemistry: float


@router.post("/verify-marks")
def verify_marks_update(
    data: VerifyMarksUpdateInput,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    user = _get_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    body     = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    if expected != data.razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    payment = db.query(Payment).filter(
        Payment.razorpay_order_id == data.razorpay_order_id
    ).first()
    if payment:
        payment.razorpay_payment_id = data.razorpay_payment_id
        payment.status = "paid"

    user.maths     = data.maths
    user.physics   = data.physics
    user.chemistry = data.chemistry
    user.aggregate = data.maths + data.physics/2 + data.chemistry/2
    db.commit()

    return {"status": "marks updated", "aggregate": user.aggregate}