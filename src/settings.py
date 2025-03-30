from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TESTING: bool = False

    SECRET_KEY: str

    PROD_DATABASE_URL: str

    CELERY_BROKER_URL: str

    SMTP_SERVER: str

    SMTP_PORT: int

    SMTP_USER: str

    SMTP_PASSWORD: str

    ALGORITHM: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int

    MINIO_ENDPOINT: str

    MINIO_ACCESS_KEY: str

    MINIO_SECRET_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()


class TestSettings(BaseSettings):
    TEST_DATABASE_URL: str

    TEST_ALEMBIC_DATABASE_URL: str

    class Config:
        env_file = ".env.test"


test_settings = TestSettings()
