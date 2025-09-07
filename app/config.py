from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # -----------------------------
    # Database
    # -----------------------------
    DATABASE_URL: str

    # -----------------------------
    # JWT
    # -----------------------------
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7


    MASTER_REFERRAL_CODE: str = "MASTERKEY"
    
    # -----------------------------
    # Stripe
    # -----------------------------
    STRIPE_SECRET_KEY: str  # e.g. "sk_test_..."
    STRIPE_WEBHOOK_SECRET: str  # from Stripe dashboard

    # -----------------------------
    # Supabase (optional for storage/KYC)
    # -----------------------------
    supabase_url: str
    supabase_key: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
