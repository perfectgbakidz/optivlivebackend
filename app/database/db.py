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
    raise ValueError(" DATABASE_URL is not set in the environment.")

# Ensure async driver is used
if DATABASE_URL.startswith("postgresql+psycopg2"):
    DATABASE_URL = DATABASE_URL.replace("psycopg2", "asyncpg")

# Setup SSL context for asyncpg
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE  # Change to CERT_REQUIRED for full verification

# Create async engine with SSL
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
    connect_args={"ssl": ssl_context},
    pool_size=5, 
    max_overflow=10, 
    pool_timeout=30, 
    pool_recycle=1800,
)

# Async session factory
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# FastAPI dependency
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
