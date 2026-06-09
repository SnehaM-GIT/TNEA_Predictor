import os
from fastapi import FastAPI, Request, Response
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

@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str, request: Request):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Credentials": "true",
        }
    )

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

@app.get("/config")
def get_config():
    return {
        "rank_list_released": os.getenv("RANK_LIST_RELEASED", "false").lower() == "true"
    }

@app.get("/health")
def health():
    return {"status": "ok"}