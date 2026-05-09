from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://asyncledger:asyncledger@localhost:5432/asyncledger"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "dev-secret"
    environment: str = "development"

    daily_limit_brl: float = 50000.00
    business_hours_start: int = 8
    business_hours_end: int = 20
    max_retry_attempts: int = 3

    class Config:
        env_file = ".env"


settings = Settings()
