import os
from typing import Optional
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
    
            

    # Project Configuration
    project_name: str = f"vto-{env}"

    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Server Configuration
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    server_port: int = int(os.getenv("SERVER_PORT", "9199"))

    # JWT Configuration
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # OAuth Configuration
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    kakao_client_id: str = os.getenv("KAKAO_CLIENT_ID", "")
    kakao_client_secret: str = os.getenv("KAKAO_CLIENT_SECRET", "")

    class Config:
        case_sensitive = False


class LocalSettings(Settings):
    env: str = "local"
    local_db_port: int = 54322
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.local_db_port}/{self.db_name}"


class DevSettings(Settings):
    env: str = "dev"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"


class ProdSettings(Settings):
    env: str = "prod"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

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