from pydantic import BaseSettings, AnyHttpUrl


class Settings(BaseSettings):
    database_url: str
    arcgis_endpoint: AnyHttpUrl
    http_timeout: int = 10
    http_retry_count: int = 2
    log_level: str = "INFO"
    app_env: str = "development"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
