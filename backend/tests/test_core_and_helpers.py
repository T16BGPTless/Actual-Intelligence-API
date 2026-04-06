"""Coverage-focused tests for app/config/helpers."""

from types import SimpleNamespace

from supabase_auth.errors import AuthApiError

from app import config
from app.app import app as flask_app
from app.routes import helpers


def test_home_redirect(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "docs.gptless.au" in resp.headers["Location"]


def test_config_env_access(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "http://example")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon")
    assert config.supabase_url() == "http://example"
    assert config.supabase_anon_key() == "anon"


def test_require_access_token_missing_header():
    with flask_app.test_request_context("/"):
        token, error = helpers.require_access_token()
        assert token is None
        assert error[1] == 401


def test_require_access_token_valid_header():
    with flask_app.test_request_context("/", headers={"Authorization": "Bearer abc"}):
        token, error = helpers.require_access_token()
        assert token == "abc"
        assert error is None


def test_require_supabase_user_unauthorized_on_auth_error(monkeypatch):
    def raise_auth(_token):
        raise AuthApiError("bad", 401, None)

    monkeypatch.setattr(
        helpers,
        "anon_client",
        lambda: SimpleNamespace(auth=SimpleNamespace(get_user=raise_auth)),
    )
    with flask_app.app_context():
        user, error = helpers.require_supabase_user("bad")
    assert user is None
    assert error[1] == 401


def test_require_supabase_user_unauthorized_on_empty_user(monkeypatch):
    monkeypatch.setattr(
        helpers,
        "anon_client",
        lambda: SimpleNamespace(
            auth=SimpleNamespace(get_user=lambda _t: SimpleNamespace(user=None))
        ),
    )
    with flask_app.app_context():
        user, error = helpers.require_supabase_user("tok")
    assert user is None
    assert error[1] == 401


def test_require_supabase_user_success(monkeypatch):
    fake_user = SimpleNamespace(id="u1")
    monkeypatch.setattr(
        helpers,
        "anon_client",
        lambda: SimpleNamespace(
            auth=SimpleNamespace(get_user=lambda _t: SimpleNamespace(user=fake_user))
        ),
    )
    user, error = helpers.require_supabase_user("tok")
    assert error is None
    assert user.id == "u1"
