"""Supabase client factories (anon auth + per-request user JWT for RLS)."""

from supabase import Client, create_client

from app.config import supabase_anon_key, supabase_service_role_key, supabase_url


def anon_client() -> Client:
    return create_client(supabase_url(), supabase_anon_key())


def service_client() -> Client:
    return create_client(supabase_url(), supabase_service_role_key())


def user_client(access_token: str) -> Client:
    client = create_client(supabase_url(), supabase_anon_key())
    client.postgrest.auth(access_token)
    return client
