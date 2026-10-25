"""Application configuration, read from the environment and an optional .env file."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings. Only the composition root (cli.py) and Alembic's env.py should read these."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DEAL_DASHBOARD_",
        extra="ignore",
    )

    database_url: str = "sqlite:///data/deal_dashboard.db"
