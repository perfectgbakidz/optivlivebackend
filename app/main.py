from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <--- add this
from .routers import auth, users, admin
from . import  models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Optivus Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://optivlive.onrender.com",
        "https://optivlive.vercel.app/",   # your frontend domain
        "http://localhost:3000"             # local dev
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # can also use ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],    # allow GET, POST, PUT, etc.
    allow_headers=["*"], 
    expose_headers=["*"],   # allow all headers
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)

