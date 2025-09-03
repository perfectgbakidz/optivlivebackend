from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    auth,
    users,
    kyc,
    transactions,
    withdrawals,
    admin,
    public,
    team,
    dashboard,
)

app = FastAPI(
    title="Optivus Backend",
    version="1.0.0",
    description="FastAPI backend with Supabase + Stripe",
)

# 🚀 Prevent 307 redirects that drop Authorization headers
app.router.redirect_slashes = False

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://optivlive.vercel.app",
]

# Allow frontend to call API
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(kyc.router)
app.include_router(transactions.router)
app.include_router(withdrawals.router)
app.include_router(admin.router)
app.include_router(dashboard.router)
app.include_router(public.router)
app.include_router(team.router)  # 👈 NEW line

@app.get("/")
async def root():
    return {"message": "Optivus API is running 🚀"}
