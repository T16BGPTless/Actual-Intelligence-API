"""Supabase client factories (anon auth + per-request user JWT for RLS)."""

from supabase import Client, create_client

from app.config import supabase_anon_key, supabase_service_role_key, supabase_url


def anon_client() -> Client:
    return create_client(supabase_url(), supabase_anon_key())


def service_client() -> Client:
    return create_client(supabase_url(), supabase_service_role_key())


def user_client(access_token: str) -> Client:
    client = create_client(supabase_url(), supabase_anon_key())

    # 1) What your tests expect
    #    (call auth() exactly with the provided token)
    client.postgrest.auth(access_token)

    # 2) Extra safety for real SDKs:
    #    If the postgrest client exposes headers, force Authorization too.
    try:
        token = access_token.removeprefix("Bearer ").strip()
        if hasattr(client.postgrest, "headers"):
            client.postgrest.headers["Authorization"] = f"Bearer {token}"
    except Exception:
        pass

    return client
