from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import models, database
from .routers import auth, users, admin, withdrawals, kyc, transactions, dashboard,team

# ✅ Initialize database tables
models.Base.metadata.create_all(bind=database.engine)


app = FastAPI(title="Optivus Backend")

# ✅ Allowed origins
origins = [
    "https://optivlive.onrender.com",   # backend (if needed)
    "https://optivlive.vercel.app",     # frontend
    "216.24.57.7:443",            # local React dev
    "http://localhost:5173"             # local Vite dev
]

# ✅ Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # change to origins if you want restricted access
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ✅ Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(withdrawals.router)
app.include_router(kyc.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)
app.include_router(team.router)
