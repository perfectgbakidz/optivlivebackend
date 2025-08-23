from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Example: postgresql://postgres:<PASSWORD>@db.<PROJECT_ID>.supabase.co:5432/postgres
    DATABASE_URL: str = ""
    JWT_SECRET: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

# ✅ Debug prints (remove later)
if __name__ == "__main__":
    print("DATABASE_URL:", settings.DATABASE_URL)
    print("JWT_SECRET:", settings.JWT_SECRET)
