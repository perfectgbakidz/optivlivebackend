import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from typing import AsyncGenerator

# Load env
load_dotenv()

DATABASE_URL: str | None = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")

# Ensure async driver
if DATABASE_URL.startswith("postgresql+psycopg2"):
    DATABASE_URL = DATABASE_URL.replace("psycopg2", "asyncpg")

# SSL only if explicitly enabled
ssl_context = None
if os.getenv("DB_SSL", "true").lower() in ("1", "true", "yes"):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE  # 🔒 change to CERT_REQUIRED in production

connect_args = {"ssl": ssl_context} if ssl_context else {}

# Async engine with pool tuning
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    connect_args=connect_args,
    pool_size=5,         # keep small pool
    max_overflow=10,     # allow a few bursts
    pool_timeout=30,     # fail fast if pool is stuck
    pool_recycle=1800,   # recycle connections every 30min
)

# Session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
