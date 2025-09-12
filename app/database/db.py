import os
import ssl
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from typing import AsyncGenerator

# Load environment variables
load_dotenv()

DATABASE_URL: str | None = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")

# --- Ensure async driver (Supabase gives psycopg2 by default) ---
if DATABASE_URL.startswith("postgresql+psycopg2"):
    DATABASE_URL = DATABASE_URL.replace("psycopg2", "asyncpg")

# --- SSL handling ---
ssl_context = None
if os.getenv("DB_SSL", "true").lower() in ("1", "true", "yes"):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED  # ✅ safer than CERT_NONE

connect_args = {"ssl": ssl_context} if ssl_context else {}

# --- Async engine with pool tuning ---
engine = create_async_engine(
    DATABASE_URL,
    echo=True,             # set False in production
    future=True,
    connect_args=connect_args,
    pool_size=5,           # small pool for Render free tier
    max_overflow=10,       # allow bursts
    pool_timeout=30,       # fail fast if pool is exhausted
    pool_recycle=1800,     # recycle every 30min
)

# --- Session factory ---
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# --- FastAPI dependency ---
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ✅ Optional: Health check for DB connection
async def test_connection() -> None:
    """Quick check to verify DB connection at startup."""
    try:
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
