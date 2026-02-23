
from typing import Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # App Settings
    # Environment Var: ATTACKMATE_CONFIG_PATH
    attackmate_config_path: Optional[str] = Field(default=None, alias="ATTACKMATE_CONFIG_PATH")
    token_expire_minutes: int = 30

    # SSL Settings
    ssl_key_file: str = "key.pem"
    ssl_cert_file: str = "cert.pem"
    debug_logging: bool = False  # Set DEBUG_LOGGING=true in .env to enable file logging
    log_dir: str = "attackmate_server_logs"

    # User Hashes: Key is username (lowercase), Value is argon2 hash
    # Environment Var: users='{"user1": "hash1"}'
    users: Dict[str, str] = {}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allows extra env vars without crashing
        extra="ignore"
    )


settings = Settings()
