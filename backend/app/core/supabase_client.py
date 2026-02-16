"""
Supabase client (service role) for backend operations.
Uses service_role key - bypasses RLS, full access.
"""

from typing import Optional
from supabase import create_client, Client

from .config import settings


_supabase_client: Optional[Client] = None


def get_supabase() -> Client:
    """Get or create Supabase client with service role."""
    global _supabase_client
    if _supabase_client is None:
        url = (settings.SUPABASE_URL or "").strip()
        key = (settings.SUPABASE_SERVICE_ROLE_KEY or "").strip()
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env"
            )
        if key in ("your-service-role-key", "your_service_role_key"):
            raise RuntimeError(
                "Replace SUPABASE_SERVICE_ROLE_KEY with your real key from "
                "Supabase Dashboard → Project Settings → API"
            )
        try:
            _supabase_client = create_client(url, key)
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to Supabase: {e}. "
                "Check SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in backend/.env"
            ) from e
    return _supabase_client
