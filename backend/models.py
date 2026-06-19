from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class GradeEnum(enum.Enum):
    one = "1"
    two = "2"
    three = "3"

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String, unique=True, nullable=True)
    mobile        = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    name          = Column(String, nullable=True)
    community     = Column(String, nullable=True)        # OC / BC / BCM / MBC / SC / ST
    grade         = Column(String, default="3")          # "1", "2", "3"
    maths         = Column(Float, nullable=True)
    physics       = Column(Float, nullable=True)
    chemistry     = Column(Float, nullable=True)
    aggregate     = Column(Float, nullable=True)         # cutoff formula score
    marks_locked     = Column(Boolean, default=False)     # locked after payment
    category_locked  = Column(Boolean, default=False)     # locked after first category save
    rank          = Column(Integer, nullable=True)
    rank_phase    = Column(String, nullable=True)        # "pre" or "post"
    has_paid      = Column(Boolean, default=False)
    preferred_colleges = Column(String, nullable=True)  # JSON string
    preferred_courses   = Column(String, nullable=True)  # JSON string
    application_id = Column(String, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    predictions   = relationship("Prediction", back_populates="user")
    payments      = relationship("Payment", back_populates="user")
    reset_tokens = relationship("PasswordResetToken", back_populates="user")


class Prediction(Base):
    __tablename__ = "predictions"

    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("users.id"), nullable=True)
    maths                = Column(Float)
    physics              = Column(Float)
    chemistry            = Column(Float)
    aggregate            = Column(Float)
    community            = Column(String)
    predicted_rank_low   = Column(Integer, nullable=True)
    predicted_rank_high  = Column(Integer, nullable=True)
    college_code         = Column(String, nullable=True)
    branch_code          = Column(String, nullable=True)
    probability          = Column(Float, nullable=True)
    created_at           = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")


class Payment(Base):
    __tablename__ = "payments"

    id                   = Column(Integer, primary_key=True, index=True)
    user_id              = Column(Integer, ForeignKey("users.id"))
    razorpay_order_id    = Column(String, unique=True)
    razorpay_payment_id  = Column(String, nullable=True)
    amount               = Column(Integer, default=14900)   # paise
    status               = Column(String, default="created") # created / paid / failed
    created_at           = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="payments")


class RankInput(Base):
    __tablename__ = "rank_inputs"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    actual_rank = Column(Integer)
    aggregate   = Column(Float)
    community   = Column(String)
    year        = Column(Integer)
    created_at  = Column(DateTime, default=datetime.utcnow)


class CutoffCache(Base):
    __tablename__ = "cutoff_cache"

    id                   = Column(Integer, primary_key=True, index=True)
    college_code         = Column(String)
    branch_code          = Column(String)
    community            = Column(String)
    predicted_cutoff_rank = Column(Integer)
    last_year_cutoff      = Column(Integer, nullable=True)
    updated_at            = Column(DateTime, default=datetime.utcnow)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token      = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used       = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_tokens")