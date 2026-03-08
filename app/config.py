from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str
    api_base_url: str
    fetch_chunk_size: int = 10
    api_key: str

    # Beat schedule (in minutes)
    fetch_users_interval: int = 10
    fetch_posts_interval: int = 15
    fetch_comments_interval: int = 20

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
