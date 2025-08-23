from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

# For Postgres (Supabase), no connect_args needed
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # helps with dropped connections
    echo=True            # optional: logs SQL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
