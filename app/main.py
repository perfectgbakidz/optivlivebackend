from fastapi import FastAPI
from .routers import auth, users, admin,admin_setup
from . import models, database

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Optivus Backend")

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(admin.router)
app.include_router(admin_setup.router)
