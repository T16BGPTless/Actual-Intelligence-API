"""Unit tests for auth routes."""

from types import SimpleNamespace

from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

from app.routes import auth as auth_routes
from tests.conftest import QueryChain


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
            "username": "taken",
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
            "username": "ok",
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
    called = {}

    def fake_sign_out(jwt, scope):
        called["jwt"] = jwt
        called["scope"] = scope

    fake_client = SimpleNamespace(
        auth=SimpleNamespace(admin=SimpleNamespace(sign_out=fake_sign_out))
    )
    monkeypatch.setattr(auth_routes, "service_client", lambda: fake_client)
    resp = client.post("/v1/auth/logout")
    assert resp.status_code == 200
    assert resp.json["message"] == "Logged out successfully"
    assert called == {"jwt": "tok", "scope": "local"}


def test_logout_invalid_token_returns_401(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "require_access_token", lambda: ("bad", None))

    def fake_sign_out(_jwt, _scope):
        raise AuthApiError("invalid", 401, None)

    fake_client = SimpleNamespace(
        auth=SimpleNamespace(admin=SimpleNamespace(sign_out=fake_sign_out))
    )
    monkeypatch.setattr(auth_routes, "service_client", lambda: fake_client)
    resp = client.post("/v1/auth/logout")
    assert resp.status_code == 401


def test_me_success_returns_user(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        auth_routes, "require_supabase_user", lambda _t: (_fake_user(), None)
    )
    monkeypatch.setattr(
        auth_routes, "_user_payload", lambda _t, _u: {"email": "u@example.com"}
    )
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 200
    assert resp.json["email"] == "u@example.com"


def test_register_falls_back_to_login_when_session_missing(client, monkeypatch):
    signup_resp = SimpleNamespace(session=None, user=_fake_user())
    signin_resp = SimpleNamespace(
        session=SimpleNamespace(access_token="fallback-token"),
        user=_fake_user(),
    )
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_up=lambda *_a, **_k: signup_resp,
            sign_in_with_password=lambda *_a, **_k: signin_resp,
        )
    )
    updated = {}
    fake_service_client = SimpleNamespace(
        auth=SimpleNamespace(
            admin=SimpleNamespace(
                update_user_by_id=lambda user_id, payload: updated.update(
                    {"user_id": user_id, "payload": payload}
                )
            )
        )
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    monkeypatch.setattr(auth_routes, "service_client", lambda: fake_service_client)
    monkeypatch.setattr(
        auth_routes, "_user_payload", lambda _t, _u: {"email": "u@example.com"}
    )
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "username": "ok",
        },
    )
    assert resp.status_code == 201
    assert resp.json["accessToken"] == "fallback-token"
    assert updated == {"user_id": "user-1", "payload": {"email_confirm": True}}


def test_register_forbidden_when_signup_has_no_session_and_fallback_fails(
    client, monkeypatch
):
    signup_resp = SimpleNamespace(session=None, user=_fake_user())

    def signin_fail(*_a, **_k):
        raise AuthApiError("confirm email", 401, None)

    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_up=lambda *_a, **_k: signup_resp, sign_in_with_password=signin_fail
        )
    )
    fake_service_client = SimpleNamespace(
        auth=SimpleNamespace(
            admin=SimpleNamespace(update_user_by_id=lambda *_a, **_k: None)
        )
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    monkeypatch.setattr(auth_routes, "service_client", lambda: fake_service_client)
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "username": "ok",
        },
    )
    assert resp.status_code == 403


def test_register_internal_error_when_user_missing(client, monkeypatch):
    fake_resp = SimpleNamespace(session=SimpleNamespace(access_token="tok"), user=None)
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(sign_up=lambda *_a, **_k: fake_resp)
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "username": "ok",
        },
    )
    assert resp.status_code == 500


def test_register_internal_error_when_session_and_user_missing(client, monkeypatch):
    fake_resp = SimpleNamespace(session=None, user=None)
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(sign_up=lambda *_a, **_k: fake_resp)
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "username": "ok",
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
    monkeypatch.setattr(
        auth_routes, "require_access_token", lambda: (None, (None, 401))
    )
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 401


def test_me_unauthorized_when_user_lookup_fails(client, monkeypatch):
    monkeypatch.setattr(auth_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        auth_routes, "require_supabase_user", lambda _t: (None, (None, 401))
    )
    resp = client.get("/v1/auth/me")
    assert resp.status_code == 401


def test_register_bad_request_for_non_conflict_auth_error(client, monkeypatch):
    def raise_other(*_a, **_k):
        raise AuthApiError("weak password", 400, None)

    fake_client = SimpleNamespace(auth=SimpleNamespace(sign_up=raise_other))
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "username": "ok",
        },
    )
    assert resp.status_code == 400


def test_register_passes_email_redirect_when_configured(client, monkeypatch):
    captured = {}

    def fake_sign_up(payload):
        captured["payload"] = payload
        return SimpleNamespace(
            session=SimpleNamespace(access_token="tok"), user=_fake_user()
        )

    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_up=fake_sign_up, sign_in_with_password=lambda *_a, **_k: None
        )
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    monkeypatch.setattr(
        auth_routes, "_user_payload", lambda _t, _u: {"email": "u@example.com"}
    )
    monkeypatch.setattr(
        auth_routes,
        "supabase_email_redirect_to",
        lambda: "https://app.example.com/auth/callback",
    )

    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "username": "ok",
        },
    )
    assert resp.status_code == 201
    assert (
        captured["payload"]["options"]["email_redirect_to"]
        == "https://app.example.com/auth/callback"
    )


def test_register_forbidden_when_fallback_has_no_session(client, monkeypatch):
    signup_resp = SimpleNamespace(session=None, user=_fake_user())
    signin_resp = SimpleNamespace(session=None, user=_fake_user())
    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_up=lambda *_a, **_k: signup_resp,
            sign_in_with_password=lambda *_a, **_k: signin_resp,
        )
    )
    fake_service_client = SimpleNamespace(
        auth=SimpleNamespace(
            admin=SimpleNamespace(update_user_by_id=lambda *_a, **_k: None)
        )
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    monkeypatch.setattr(auth_routes, "service_client", lambda: fake_service_client)
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "username": "ok",
        },
    )
    assert resp.status_code == 403


def test_register_internal_error_when_autoconfirm_fails(client, monkeypatch):
    signup_resp = SimpleNamespace(session=None, user=_fake_user())

    def update_fail(*_a, **_k):
        raise AuthApiError("nope", 400, None)

    fake_client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_up=lambda *_a, **_k: signup_resp,
            sign_in_with_password=lambda *_a, **_k: None,
        )
    )
    fake_service_client = SimpleNamespace(
        auth=SimpleNamespace(admin=SimpleNamespace(update_user_by_id=update_fail))
    )
    monkeypatch.setattr(auth_routes, "anon_client", lambda: fake_client)
    monkeypatch.setattr(auth_routes, "service_client", lambda: fake_service_client)
    resp = client.post(
        "/v1/auth/register",
        json={
            "email": "ok@example.com",
            "password": "pw",
            "name": "User",
            "username": "ok",
        },
    )
    assert resp.status_code == 500


def test_user_payload_prefers_profile_data(monkeypatch):
    fake_user = _fake_user()
    chain = QueryChain(
        {
            "username": "from_profile",
            "display_name": "Profile Name",
            "created_at": "2026-04-02T00:00:00+00:00",
        }
    )
    monkeypatch.setattr(
        auth_routes, "user_client", lambda _t: SimpleNamespace(table=lambda _n: chain)
    )
    payload = auth_routes._user_payload("tok", fake_user)
    assert payload["username"] == "from_profile"
    assert payload["name"] == "Profile Name"


def test_user_payload_falls_back_to_metadata_on_profile_error(monkeypatch):
    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "boom"})

    monkeypatch.setattr(
        auth_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: BadChain()),
    )
    payload = auth_routes._user_payload("tok", _fake_user())
    assert payload["username"] == "u1"
    assert payload["name"] == "User One"


