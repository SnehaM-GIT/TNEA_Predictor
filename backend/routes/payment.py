from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db
from models import User, Payment
from auth_middleware import require_grade
from typing import Optional
import razorpay
import hmac
import hashlib
import os
import jwt

router = APIRouter()

RAZORPAY_KEY_ID     = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
SECRET_KEY          = os.getenv("SECRET_KEY", "pickmyseat_secret")

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
    user = _get_user(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if user.has_paid:
        raise HTTPException(status_code=400, detail="Already purchased")

    client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    order  = client.order.create({
        "amount":   14900,
        "currency": "INR",
        "payment_capture": 1
    })

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

    # verify HMAC signature
    body      = f"{data.razorpay_order_id}|{data.razorpay_payment_id}"
    expected  = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        body.encode(),
        hashlib.sha256
    ).hexdigest()

    if expected != data.razorpay_signature:
        raise HTTPException(status_code=400, detail="Invalid payment signature")

    # update payment record
    payment = db.query(Payment).filter(
        Payment.razorpay_order_id == data.razorpay_order_id
    ).first()
    if payment:
        payment.razorpay_payment_id = data.razorpay_payment_id
        payment.status = "paid"

    # upgrade user to Grade 1 and lock marks
    user.has_paid    = True
    user.grade       = "1"
    user.marks_locked = True
    db.commit()

    return {"status": "payment verified", "grade": "1"}