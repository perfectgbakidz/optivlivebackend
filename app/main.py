from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware  # <--- add this
from .routers import auth, users, admin, admin_setup
from . import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Optivus Backend")

origins = [
    "https://optivlive.onrender.com",  # your frontend URL
    "http://localhost:3000"            # optional, for local dev
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # can also use ["*"] to allow all origins
    allow_credentials=True,
    allow_methods=["*"],    # allow GET, POST, PUT, etc.
    allow_headers=["*"],    # allow all headers
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(admin_setup.router)
