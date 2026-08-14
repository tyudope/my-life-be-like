from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding = "utf-8",
        extra="ignore",
    )
    database_url:str
    anthropic_api_key:str

    


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

