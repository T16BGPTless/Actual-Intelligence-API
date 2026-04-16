"""Environment-driven configuration for the API."""

import os
import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache
def _local_supabase_env() -> dict[str, str]:
    """Best-effort fallback for local dev when SUPABASE_* vars are unset."""
    try:
        result = subprocess.run(
            ["npx", "supabase", "status", "-o", "env"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return {}

    env = {}
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def _required_env(var_name: str, fallback_name: str | None = None) -> str:
    value = os.environ.get(var_name)
    if value:
        return value

    if fallback_name:
        fallback_value = _local_supabase_env().get(fallback_name)
        if fallback_value:
            os.environ[var_name] = fallback_value
            return fallback_value

    raise RuntimeError(
        f"{var_name} is required. Export env vars with "
        '`eval "$(npx supabase status -o env)"` and map to SUPABASE_* values.'
    )


def supabase_url() -> str:
    return _required_env("SUPABASE_URL", fallback_name="API_URL")


def supabase_anon_key() -> str:
    return _required_env("SUPABASE_ANON_KEY", fallback_name="ANON_KEY")


def supabase_service_role_key() -> str:
    return _required_env("SUPABASE_SERVICE_ROLE_KEY", fallback_name="SERVICE_ROLE_KEY")


def supabase_email_redirect_to() -> str | None:
    """Optional email verification redirect URL for Supabase auth links."""
    return os.environ.get("SUPABASE_EMAIL_REDIRECT_TO")
