from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./price_monitor.db"
    dev_api_keys: List[str] = ["dev-key"]

    cors_origins: List[str] = ["http://localhost:5173", "http://localhost:5174"]

    sample_data_dir: str = "./sample_products"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
