"""Environment-driven configuration for the API."""

import os


def supabase_url() -> str:
    return os.environ["SUPABASE_URL"]


def supabase_anon_key() -> str:
    return os.environ["SUPABASE_ANON_KEY"]


def supabase_service_role_key() -> str:
    return os.environ["SUPABASE_SERVICE_ROLE_KEY"]


def supabase_email_redirect_to() -> str | None:
    """Optional email verification redirect URL for Supabase auth links."""
    return os.environ.get("SUPABASE_EMAIL_REDIRECT_TO")
