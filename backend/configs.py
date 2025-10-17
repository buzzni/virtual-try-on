import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from custom_logger import get_logger

# Load .env file
load_dotenv()

logger = get_logger(__name__)

class Settings(BaseSettings):
    # Environment
    env: str = os.getenv("ENV", "local")

    # Database Configuration
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_user: str = os.getenv("DB_USER", "vto_user")
    db_password: str = os.getenv("DB_PASSWORD", "vto_password")
    db_name: str = os.getenv("DB_NAME", "vto_db")

    # Database URL
    @property
    def database_url(self) -> str:
        if self.env == "local":
            # PostgreSQL for local environment
            return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.env == "dev":
            # SQLite for dev environment (can be changed)
            return "sqlite+aiosqlite:///./vto_dev.db"
        else:
            # PostgreSQL for production
            return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

    # Project Configuration
    project_name: str = f"vto-{env}"

    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", None)
    openai_api_key: str = os.getenv("OPENAI_API_KEY", None)

    # Server Configuration
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", "9199"))

    class Config:
        case_sensitive = False


class LocalSettings(Settings):
    env: str = "local"


class DevSettings(Settings):
    env: str = "dev"


class ProdSettings(Settings):
    env: str = "prod"


def get_settings():
    env = os.getenv("ENV", "local")
    if env == "local":
        return LocalSettings()
    elif env == "dev":
        return DevSettings()
    elif env == "prod":
        return ProdSettings()
    else:
        logger.warning(f"Unknown environment: {env}, using local settings")
        return LocalSettings()


settings: Settings = get_settings()
logger.info(f"ENV: {settings.env}")
logger.info(f"Database URL: {settings.database_url}")