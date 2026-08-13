from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    arcgis_endpoint: AnyHttpUrl = Field(validation_alias="ARC_GIS_ENDPOINT")
    http_timeout: int = 10
    http_retry_count: int = 2
    log_level: str = "INFO"
    app_env: str = "development"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)


settings = Settings()
