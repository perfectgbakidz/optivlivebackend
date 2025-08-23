from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./optivus.db"
    JWT_SECRET: str = "supersecretkey"  # change to env var in production

    class Config:
        env_file = ".env"

settings = Settings()
