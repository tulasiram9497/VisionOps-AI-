from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    app_name: str = "VisionOps AI"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./visionops.db"
    camera_index: int = 0
    frame_width: int = 640
    frame_height: int = 480
    model_name: str = "yolo11n.pt"
    confidence_threshold: float = 0.5
    tracker_type: str = "bytetrack"
    enable_ai: bool = False
    llm_provider: str = ""
    llm_api_key: str = ""
    webhook_url: str = ""
    alert_webhook_url: str = ""
    model_dir: str = "./models"
    env_file: str = ".env"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )


settings = Settings()
