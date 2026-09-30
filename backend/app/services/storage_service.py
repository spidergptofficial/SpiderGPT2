"""SpiderGPT Storage Service.

Handles secure file persistence (Local disk / Supabase Storage) with MIME and size validation.
"""
import os
import uuid
from typing import Dict, Any, Optional
import aiofiles

from backend.app.core.config import settings
from backend.app.core.exceptions import ValidationErrorException
from backend.app.core.logging import logger

ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class StorageService:
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER
        self.local_dir = settings.STORAGE_LOCAL_DIR
        if self.provider == "local":
            os.makedirs(self.local_dir, exist_ok=True)

    async def save_file(self, file_bytes: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Validates MIME type, enforces size limits, and securely persists binary file."""
        if len(file_bytes) > MAX_FILE_SIZE:
            raise ValidationErrorException("File size exceeds maximum allowed 10MB limit.")

        if content_type not in ALLOWED_IMAGE_MIMES:
            raise ValidationErrorException(f"Unsupported media type: {content_type}. Allowed: {ALLOWED_IMAGE_MIMES}")

        extension_by_mime = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
        clean_filename = f"{uuid.uuid4().hex}.{extension_by_mime[content_type]}"

        if self.provider == "supabase" and settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            # Upload to Supabase Storage bucket via HTTPX
            import httpx
            url = f"{settings.SUPABASE_URL}/storage/v1/object/{settings.STORAGE_BUCKET_NAME}/{clean_filename}"
            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": content_type,
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, headers=headers, content=file_bytes)
                if resp.status_code in [200, 201]:
                    public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.STORAGE_BUCKET_NAME}/{clean_filename}"
                    return {"url": public_url, "filename": clean_filename, "size": len(file_bytes)}

        if self.provider != "local":
            raise ValidationErrorException("Configured storage provider is unavailable.")

        file_path = os.path.join(self.local_dir, clean_filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        url = f"{settings.APPLICATION_BASE_URL}/uploads/{clean_filename}"
        return {"url": url, "filename": clean_filename, "size": len(file_bytes)}
