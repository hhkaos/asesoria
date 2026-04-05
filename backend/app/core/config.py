from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    DATABASE_URL: str
    DATABASE_TEST_URL: str
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    FILES_BASE_PATH: str = "./data/files"
    MAX_UPLOAD_SIZE_MB: int = 10
    ENVIRONMENT: str = "dev"


settings = Settings()
