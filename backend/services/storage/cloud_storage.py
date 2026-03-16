from __future__ import annotations

import base64
import logging

from config import get_settings

logger = logging.getLogger(__name__)

_gcs_client: GCSClient | None = None


class GCSClient:
    """Google Cloud Storage client for screenshot uploads."""

    def __init__(self) -> None:
        self.bucket = None
        settings = get_settings()
        if settings.gcs_bucket:
            try:
                from google.cloud import storage
                client = storage.Client()
                self.bucket = client.bucket(settings.gcs_bucket)
                logger.info("GCS connected to bucket: %s", settings.gcs_bucket)
            except Exception as e:
                logger.warning("GCS not available: %s", e)

    def upload_screenshot(self, session_id: str, step_num: int, png_b64: str) -> str:
        """Upload screenshot and return public URL or empty string."""
        if self.bucket is None:
            return ""
        blob_name = f"sessions/{session_id}/step_{step_num}.png"
        blob = self.bucket.blob(blob_name)
        png_bytes = base64.b64decode(png_b64)
        blob.upload_from_string(png_bytes, content_type="image/png")
        return blob.public_url

    def get_screenshot_url(self, session_id: str, step_num: int) -> str:
        if self.bucket is None:
            return ""
        blob_name = f"sessions/{session_id}/step_{step_num}.png"
        return f"https://storage.googleapis.com/{self.bucket.name}/{blob_name}"


def get_gcs_client() -> GCSClient:
    global _gcs_client
    if _gcs_client is None:
        _gcs_client = GCSClient()
    return _gcs_client
