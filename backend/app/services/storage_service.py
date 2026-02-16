"""
Supabase storage service - upload files, generate signed URLs.
"""

import logging
import os
import tempfile
from typing import Optional

from app.core.config import settings
from app.core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

BUCKET = "cv-originals"


async def upload_file(
    file_content: bytes,
    filename: str,
    user_id: str,
    cv_id: str,
) -> str:
    """
    Upload file to Supabase Storage. Path: {user_id}/{cv_id}/{filename}
    Returns the storage path.
    """
    supabase = get_supabase()
    path = f"{user_id}/{cv_id}/{filename}"

    try:
        # storage3 expects a file path (str), not BytesIO - use temp file
        ext = "." + filename.split(".")[-1] if "." in filename else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext or ".bin") as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name
        try:
            supabase.storage.from_(BUCKET).upload(
                path=path,
                file=tmp_path,
                file_options={"content-type": _get_content_type(filename)},
            )
        finally:
            os.unlink(tmp_path)
        return path
    except Exception as e:
        logger.error(f"Storage upload failed: {e}")
        raise


def create_signed_url(file_path: str, expires_in: int = 3600) -> Optional[str]:
    """
    Create a signed URL for secure access to the original document.
    """
    try:
        supabase = get_supabase()
        result = supabase.storage.from_(BUCKET).create_signed_url(
            path=file_path,
            expires_in=expires_in,
        )
        # Handle APIResponse - result may have .data or be a dict
        if hasattr(result, "data") and isinstance(result.data, dict):
            return result.data.get("signedUrl") or result.data.get("signed_url")
        if hasattr(result, "data") and isinstance(result.data, str):
            return result.data
        if isinstance(result, dict):
            return result.get("signedUrl") or result.get("signed_url")
        return None
    except Exception as e:
        logger.error(f"Signed URL creation failed: {e}")
        return None


def _get_content_type(filename: str) -> str:
    """Infer content type from filename."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return "application/pdf"
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".docx"):
        return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return "application/octet-stream"
