from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import predict, auth

app = FastAPI(title="PickMySeat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(predict.router, prefix="/predict")

@app.get("/")
def root():
    return {"status": "PickMySeat API is running"}