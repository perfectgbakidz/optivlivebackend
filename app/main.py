from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, users, admin
from . import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Optivus Backend")

# ✅ Allowed origins (no trailing slashes!)
origins = [
    "https://optivlive.onrender.com",   # backend (if needed)
    "https://optivlive.vercel.app",     # frontend
    "http://localhost:3000",
    "http://localhost:5173"            # local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # or ["*"] if you want all origins
    allow_credentials=True,
    allow_methods=["*"],         # allow GET, POST, PUT, etc.
    allow_headers=["*"],
    expose_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
