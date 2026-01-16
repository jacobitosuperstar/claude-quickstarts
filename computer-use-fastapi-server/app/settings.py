from typing import List
from typing import Optional
from pydantic_settings import BaseSettings
from app.base.logger import ConsoleLogger


class Settings(BaseSettings):
    project_name: str = "PPS BACKEND"
    debug: bool = True
    acces_token_experation: int = 60 * 24 * 7 # => The finel number(7) is days
    log_file: Optional[str] = None
    pythonpath: str = "."

    # Testing mode - disable authentication for testing
    # NOTE: This should be False in production, True only for development/testing
    # Test files will override this to True regardless of this setting
    disable_auth: bool = True
    # Database and Security
    database_url: str = "sqlite:///./db.sqlite3"
    algorithm: str = "HS256"
    secret_key: str = "encryption_token_123"

    # Anthropic API
    anthropic_api_key: Optional[str] = None

    # Agent settings
    message_batch_size: int = 10  # Batch size for database commits during agent execution

    # Cors
    backend_cors_origins: List[str] = ["*"]

    class Config:
        env_file: str = ".env"
        case_sensitive: bool = False


settings: Settings = Settings()

debug_level: str = "DEBUG" if settings.debug else "ERROR"
logger: ConsoleLogger = ConsoleLogger(
    filename=settings.log_file,
    level=debug_level,
)
