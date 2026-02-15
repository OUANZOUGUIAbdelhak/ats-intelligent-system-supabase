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
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
                "Check your .env file."
            )
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _supabase_client
