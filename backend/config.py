from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gemini API
    gemini_api_key: str = ""
    gemini_perception_model: str = "gemini-2.5-flash"
    gemini_evaluation_model: str = "gemini-2.5-flash"
    gemini_report_model: str = "gemini-2.5-flash"
    gemini_max_retries: int = 3
    gemini_timeout_seconds: int = 30

    # Browser
    browser_headless: bool = True
    screenshot_width: int = 960
    screenshot_height: int = 540
    max_steps: int = 30
    step_timeout_seconds: int = 10
    confidence_threshold: float = 0.65

    # Google Cloud
    gcp_project_id: str = ""
    gcs_bucket: str = ""
    firestore_project: str = ""

    # ADK
    adk_enabled: bool = True

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    debug: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
