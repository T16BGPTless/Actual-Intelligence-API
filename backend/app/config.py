"""Environment-driven configuration for the API."""

import os


def supabase_url() -> str:
    return os.environ["SUPABASE_URL"]


def supabase_anon_key() -> str:
    return os.environ["SUPABASE_ANON_KEY"]
