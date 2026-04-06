"""Unit tests for auth routes."""

from types import SimpleNamespace

from supabase_auth.errors import AuthApiError

from app.routes import auth as auth_routes


def _fake_user():
    return SimpleNamespace(
        id="user-1",
        email="u@example.com",
        created_at="2026-04-01T00:00:00+00:00",
        user_metadata={"username": "u1", "name": "User One"},
    )


def _patch_auth_ok(monkeypatch, token="tok"):
    fake_resp = SimpleNamespace(
        session=SimpleNamespace(access_token=token),
        user=_fake_user(),
    )
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_up=lambda *_a, **_k: fake_resp,
            sign_in_with_password=lambda *_a, **_k: fake_resp,
        )
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    monkeypatch.setattr(
        auth_routes, "_user_payload", lambda _t, _u: {"email": "u@example.com"}
    )


def test_register_missing_field_returns_400(client):
    resp = client.post("/v1/auth/register", json={"email": "x"})
    assert resp.status_code == 400
    assert resp.json["error"] == "BAD_REQUEST"


def test_register_conflict_returns_409(client, monkeypatch):
    def raise_taken(*_a, **_k):
        raise AuthApiError("already registered", 400, None)

    fake_client = SimpleNamespace(auth=SimpleNamespace(sign_up=raise_taken))
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)

    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "taken@example.com",
            "password": "pw",
            "name": "User",
            "userName": "taken",
        },
    )
    assert resp.status_code == 409
    assert resp.json["error"] == "CONFLICT"


def test_register_success_returns_201(client, monkeypatch):
    _patch_auth_ok(monkeypatch, token="token-register")

    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "userName": "ok",
        },
    )
    assert resp.status_code == 201
    assert resp.json["accessToken"] == "token-register"


def test_login_missing_password_returns_400(client):
    resp = client.post("/v1/auth/login", json={"email": "u@example.com"})
    assert resp.status_code == 400
    assert resp.json["error"] == "BAD_REQUEST"


def test_login_auth_failure_returns_401(client, monkeypatch):
    def raise_bad(*_a, **_k):
        raise AuthApiError("bad creds", 401, None)

    fake_client = SimpleNamespace(auth=SimpleNamespace(sign_in_with_password=raise_bad))
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)

    resp = client.post(
        "/v1/auth/login", json={"email": "u@example.com", "password": "wrong"}
    )
    assert resp.status_code == 401
    assert resp.json["error"] == "UNAUTHORIZED"


def test_login_success_returns_200(client, monkeypatch):
    _patch_auth_ok(monkeypatch, token="token-login")
    resp = client.post(
        "/v1/auth/login", json={"email": "u@example.com", "password": "pw"}
    )
    assert resp.status_code == 200
    assert resp.json["accessToken"] == "token-login"


def test_logout_unauthorized_returns_401(client, monkeypatch):
    monkeypatch.setattr(
        auth_routes, "require_access_token", lambda: (None, (None, 401))
    )
    resp = client.post("/v1/auth/logout")
    assert resp.status_code == 401


def test_logout_success_returns_200(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "require_access_token", lambda: ("tok", None))
    resp = client.post("/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json["message"] == "Logged out successfully"


def test_me_success_returns_user(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(auth_routes, "require_supabase_user", lambda _t: (_fake_user(), None))
    monkeypatch.setattr(
        auth_routes, "_user_payload", lambda _t, _u: {"email": "u@example.com"}
    )
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json["email"] == "u@example.com"


def test_register_forbidden_when_session_missing(client, monkeypatch):
    fake_resp = SimpleNamespace(session=None, user=_fake_user())
    fake_client = SimpleNamespace(auth=SimpleNamespace(sign_up=lambda *_a, **_k: fake_resp))
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "userName": "ok",
        },
    )
    assert resp.status_code == 403


def test_register_internal_error_when_user_missing(client, monkeypatch):
    fake_resp = SimpleNamespace(session=SimpleNamespace(access_token="tok"), user=None)
    fake_client = SimpleNamespace(auth=SimpleNamespace(sign_up=lambda *_a, **_k: fake_resp))
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "userName": "ok",
        },
    )
    assert resp.status_code == 500


def test_login_requires_email(client):
    resp = client.post("/v1/auth/login", json={"password": "pw"})
    assert resp.status_code == 400


def test_login_unauthorized_when_response_missing_user(client, monkeypatch):
    fake_resp = SimpleNamespace(session=SimpleNamespace(access_token="tok"), user=None)
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(sign_in_with_password=lambda *_a, **_k: fake_resp)
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    resp = client.post(
        "/v1/auth/login", json={"email": "u@example.com", "password": "pw"}
    )
    assert resp.status_code == 401


def test_me_unauthorized_when_auth_missing(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "require_access_token", lambda: (None, (None, 401)))
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 401


def test_me_unauthorized_when_user_lookup_fails(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(auth_routes, "require_supabase_user", lambda _t: (None, (None, 401)))
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 401
