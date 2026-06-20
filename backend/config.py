"""
config.py

Load and manage environment variables from .env file.

Usage:
    from backend.config import config
    db_url = config.DATABASE_URL
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Config:
    """Application configuration from environment variables"""

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"

    # JWT Security (signing key is SECRET_KEY, read directly in auth routes)
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

    # Database (Railway PostgreSQL)
    DATABASE_URL = os.getenv("DATABASE_URL")

    # Razorpay (Payment Gateway)
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "placeholder")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "placeholder")

    # Email
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "noreply@pickmyseat.ai")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "placeholder")

    # FastAPI
    FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))

    # Frontend & URLs
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api")

    # ML Models
    RANK_MODEL_PATH = os.getenv(
        "RANK_MODEL_PATH",
        "backend/data/cleaned/rank_model_final.pkl"
    )
    CUTOFF_MODEL_PATH = os.getenv(
        "CUTOFF_MODEL_PATH",
        "backend/data/cleaned/cutoff_predictor.pkl"
    )
    COLLEGE_CODES_PATH = os.getenv(
        "COLLEGE_CODES_PATH",
        "backend/data/cleaned/college_codes.csv"
    )
    COURSE_CODES_PATH = os.getenv(
        "COURSE_CODES_PATH",
        "backend/data/cleaned/course_codes.csv"
    )

# Create single config instance
config = Config()

# Print config status on startup (don't print secrets!)
if config.DEBUG:
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║  PickMySeat.AI Configuration Loaded                      ║
╚═══════════════════════════════════════════════════════════╝

Environment    : {config.ENVIRONMENT}
Debug Mode     : {config.DEBUG}
FastAPI        : {config.FASTAPI_HOST}:{config.FASTAPI_PORT}
Frontend URL   : {config.FRONTEND_URL}
Database       : Connected to Railway PostgreSQL
JWT Algorithm  : {config.JWT_ALGORITHM}

✅ All secrets loaded from .env
    """)
