
from typing import Dict, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    attackmate_config_path: Optional[str] = Field(default=None, alias="ATTACKMATE_CONFIG_PATH")
    token_expire_minutes: int = 30

    # SSL files; relative paths resolve against the working directory (like .env)
    ssl_key_path: str = Field(default="key.pem", alias="SSL_KEY_PATH")
    ssl_cert_path: str = Field(default="cert.pem", alias="SSL_CERT_PATH")
    write_playbook_logs_to_disk: bool = False  # Set WRITE_PLAYBOOK_LOGS_TO_DISK in .env
    log_dir: str = "attackmate_server_logs"
    attackmate_api_server_port: int = 8445

    # User Hashes: Key is username (lowercase), Value is argon2 hash
    # Environment Var: users='{"user1": "hash1"}'
    users: Dict[str, str] = {}

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
