from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql://safestep:safestep@localhost:5432/safestep"
    gemini_api_key: str = ""
    socrata_app_token: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "SafeStep/1.0"
    news_api_key: str = ""
    nyt_api_key: str = ""
    mapbox_token: str = ""
    census_api_key: str = ""

    @property
    def async_database_url(self) -> str:
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
