import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routes import predict, auth, payment

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="PickMySeat API")

ALLOWED_ORIGINS = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
    "http://127.0.0.1",
    "null",
    "https://pickymyseat.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(auth.router, prefix="/auth")
app.include_router(predict.router, prefix="/predict")
app.include_router(payment.router, prefix="/payment")


@app.on_event("startup")
async def startup_checks():
    missing = []
    for var in ["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET", "SECRET_KEY", "DATABASE_URL"]:
        if not os.getenv(var):
            missing.append(var)
    if missing:
        print(f"⚠️  WARNING: Missing environment variables: {', '.join(missing)}")
    else:
        print("✅ All required environment variables are set.")


@app.get("/")
def root():
    return {"status": "PickMySeat API is running"}