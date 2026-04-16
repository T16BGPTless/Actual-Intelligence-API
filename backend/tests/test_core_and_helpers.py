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


def test_config_service_role_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "service")
    assert config.supabase_service_role_key() == "service"


def test_local_supabase_env_handles_subprocess_failure(monkeypatch):
    config._local_supabase_env.cache_clear()

    def raise_called(*_a, **_k):
        raise OSError("boom")

    monkeypatch.setattr(config.subprocess, "run", raise_called)
    assert config._local_supabase_env() == {}


def test_local_supabase_env_parses_output(monkeypatch):
    config._local_supabase_env.cache_clear()

    monkeypatch.setattr(
        config.subprocess,
        "run",
        lambda *_a, **_k: SimpleNamespace(
            stdout="API_URL=http://x\nNOPE\nANON_KEY=abc\n"
        ),
    )
    parsed = config._local_supabase_env()
    assert parsed["API_URL"] == "http://x"
    assert parsed["ANON_KEY"] == "abc"


def test_required_env_raises_when_missing(monkeypatch):
    config._local_supabase_env.cache_clear()
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setattr(config, "_local_supabase_env", lambda: {})
    try:
        config.supabase_url()
        assert False, "Expected RuntimeError"
    except RuntimeError:
        pass


def test_required_env_uses_fallback_and_sets_env(monkeypatch):
    config._local_supabase_env.cache_clear()
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.setattr(
        config, "_local_supabase_env", lambda: {"SERVICE_ROLE_KEY": "srv"}
    )
    assert config.supabase_service_role_key() == "srv"


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


def test_require_access_token_access_token_header():
    with flask_app.test_request_context("/", headers={"AccessToken": "abc"}):
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
