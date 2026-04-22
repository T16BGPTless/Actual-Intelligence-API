"""Tests for app.supabase_client wrappers."""

from types import SimpleNamespace

from app import supabase_client


def test_anon_client_uses_env_config(monkeypatch):
    monkeypatch.setattr(supabase_client, "supabase_url", lambda: "http://supa")
    monkeypatch.setattr(supabase_client, "supabase_anon_key", lambda: "anon")

    called = {}

    def fake_create_client(url, key):
        called["url"] = url
        called["key"] = key
        return SimpleNamespace(postgrest=SimpleNamespace(auth=lambda _t: None))

    monkeypatch.setattr(supabase_client, "create_client", fake_create_client)
    client = supabase_client.anon_client()
    assert client is not None
    assert called == {"url": "http://supa", "key": "anon"}


def test_user_client_sets_postgrest_auth(monkeypatch):
    monkeypatch.setattr(supabase_client, "supabase_url", lambda: "http://supa")
    monkeypatch.setattr(supabase_client, "supabase_anon_key", lambda: "anon")

    called = {}

    def fake_auth(token):
        called["token"] = token

    fake_client = SimpleNamespace(postgrest=SimpleNamespace(auth=fake_auth))
    monkeypatch.setattr(supabase_client, "create_client", lambda _u, _k: fake_client)

    out = supabase_client.user_client("access-token")
    assert out is fake_client
    assert called["token"] == "access-token"


def test_service_client_uses_service_role_key(monkeypatch):
    monkeypatch.setattr(supabase_client, "supabase_url", lambda: "http://supa")
    monkeypatch.setattr(supabase_client, "supabase_service_role_key", lambda: "service")

    called = {}

    def fake_create_client(url, key):
        called["url"] = url
        called["key"] = key
        return SimpleNamespace(postgrest=SimpleNamespace(auth=lambda _t: None))

    monkeypatch.setattr(supabase_client, "create_client", fake_create_client)
    client = supabase_client.service_client()
    assert client is not None
    assert called == {"url": "http://supa", "key": "service"}


def test_user_client_sets_authorization_header_when_headers_available(monkeypatch):
    """Covers the postgrest.headers branch (lines 27-28 in supabase_client.py)."""
    monkeypatch.setattr(supabase_client, "supabase_url", lambda: "http://supa")
    monkeypatch.setattr(supabase_client, "supabase_anon_key", lambda: "anon")

    headers = {}
    fake_client = SimpleNamespace(
        postgrest=SimpleNamespace(
            auth=lambda _t: None,
            headers=headers,
        )
    )
    monkeypatch.setattr(supabase_client, "create_client", lambda _u, _k: fake_client)

    supabase_client.user_client("my-token")
    assert headers.get("Authorization") == "Bearer my-token"


def test_user_client_handles_missing_headers_gracefully(monkeypatch):
    """postgrest has no headers attr → exception is swallowed (line 29-30)."""
    monkeypatch.setattr(supabase_client, "supabase_url", lambda: "http://supa")
    monkeypatch.setattr(supabase_client, "supabase_anon_key", lambda: "anon")

    # postgrest with auth but no headers attr — removeprefix is fine, hasattr is False
    fake_client = SimpleNamespace(
        postgrest=SimpleNamespace(auth=lambda _t: None)
    )
    monkeypatch.setattr(supabase_client, "create_client", lambda _u, _k: fake_client)

    out = supabase_client.user_client("tok")
    assert out is fake_client
