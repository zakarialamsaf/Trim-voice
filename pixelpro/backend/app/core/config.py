from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    # App
    APP_NAME: str = "PixelPro"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/pixelpro"

    # Redis / Celery (use memory:// for local dev without Redis)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    CELERY_TASK_ALWAYS_EAGER: bool = False  # set True in local dev for sync tasks

    # AWS S3 (set AWS_ENDPOINT_URL=http://minio:9000 for MinIO, leave empty to use local file storage)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: Optional[str] = None
    S3_BUCKET_INPUT: str = "pixelpro-inputs"
    S3_BUCKET_OUTPUT: str = "pixelpro-outputs"
    S3_PRESIGNED_URL_EXPIRY: int = 3600  # seconds
    LOCAL_STORAGE_DIR: str = "./local_storage"  # used when AWS_ACCESS_KEY_ID == "dev"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_STARTER: str = ""   # price_xxx
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_BUSINESS: str = ""

    # JWT
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # AI Models
    MODELS_DIR: str = "/app/models"
    MAX_IMAGE_SIZE_MB: int = 20
    MAX_BATCH_SIZE: int = 10

    # Credits per plan (Free = 3-day trial with 500 credits)
    FREE_MONTHLY_CREDITS: int = 500
    STARTER_MONTHLY_CREDITS: int = 100
    PRO_MONTHLY_CREDITS: int = 500
    BUSINESS_MONTHLY_CREDITS: int = 2000

    # AI Edit providers
    FAL_KEY: str = ""
    HF_TOKEN: str = ""

    class Config:
        env_file = (".env", ".env.local")   # .env.local overrides .env
        case_sensitive = True


settings = Settings()
