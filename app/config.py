from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "NZ/AU Voice Partner Acquisition System"
    database_url: str = "sqlite:///./data/voice_partners.db"
    host: str = "127.0.0.1"
    port: int = 8000
    log_level: str = "INFO"

    apollo_api_key: str | None = None
    hunter_api_key: str | None = None
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"

    crawler_timeout_seconds: int = 15
    crawler_max_pages: int = 15
    crawler_delay_seconds: float = 1.0
    crawler_user_agent: str = "NZ-AU-Voice-Partner-Research/1.0"

    leads_inbox_dir: str = "./leads/inbox"
    leads_processed_dir: str = "./leads/processed"

    outreach_score_threshold: int = 65
    priority_score_threshold: int = 80

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
