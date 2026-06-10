from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    SECRET_KEY: str = "change-this-secret-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    DATA_DIR: str = "data"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def data_path(self) -> Path:
        return Path(self.DATA_DIR)


settings = Settings()
