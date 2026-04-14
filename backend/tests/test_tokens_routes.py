"""Unit tests for token routes."""

from types import SimpleNamespace

from postgrest.exceptions import APIError

from app.routes import tokens as tokens_routes
from tests.conftest import QueryChain


def _ok_auth(monkeypatch, user_id="u1"):
    monkeypatch.setattr(tokens_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        tokens_routes,
        "require_supabase_user",
        lambda _t: (SimpleNamespace(id=user_id), None),
    )


def test_get_tokens_success(client, monkeypatch):
    _ok_auth(monkeypatch)
    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )
    balance_chain = QueryChain({"balance": 42})

    def table(name):
        return account_chain if name == "accounts" else balance_chain

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
    )
    resp = client.get("/v1/tokens", json={"accountName": "Main"})
    assert resp.status_code == 200
    assert resp.json == {"accountName": "Main", "tokenBalance": 42}


def test_get_tokens_missing_account_name(client, monkeypatch):
    _ok_auth(monkeypatch)
    resp = client.get("/v1/tokens", json={})
    assert resp.status_code == 400


def test_get_tokens_not_found(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda _n: QueryChain(None)),
    )
    resp = client.get("/v1/tokens", json={"accountName": "Missing"})
    assert resp.status_code == 404


def test_get_tokens_forbidden_when_not_account_owner(client, monkeypatch):
    _ok_auth(monkeypatch)
    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "someone-else"}
    )
    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda _n: account_chain),
    )
    resp = client.get("/v1/tokens", json={"accountName": "Main"})
    assert resp.status_code == 403


def test_get_tokens_internal_on_api_error(client, monkeypatch):
    _ok_auth(monkeypatch)

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "denied", "code": "42501"})

    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda _n: BadChain()),
    )
    resp = client.get("/v1/tokens", json={"accountName": "Main"})
    assert resp.status_code == 500


def test_get_tokens_handles_none_execute_result(client, monkeypatch):
    _ok_auth(monkeypatch)

    class NoneChain(QueryChain):
        def execute(self):
            return None

    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda _n: NoneChain()),
    )
    resp = client.get("/v1/tokens", json={"accountName": "Main"})
    assert resp.status_code == 404


def test_buy_tokens_success(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")

    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )
    balance_chain = QueryChain({"balance": 10})
    write_chain = QueryChain()

    def table(name):
        if name == "accounts":
            return account_chain
        if name == "token_balances":
            return balance_chain
        return write_chain

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
    )

    resp = client.post("/v1/tokens/buy", json={"accountName": "Main", "tokens": 5})
    assert resp.status_code == 200
    assert resp.json == {"accountName": "Main", "tokensAdded": 5, "tokenBalance": 15}


def test_buy_tokens_forbidden_when_not_account_owner(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(
            table=lambda _n: QueryChain(
                {"account_id": "a1", "account_name": "Main", "created_by": "other-user"}
            )
        ),
    )
    resp = client.post("/v1/tokens/buy", json={"accountName": "Main", "tokens": 5})
    assert resp.status_code == 403


def test_buy_tokens_not_found(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda _n: QueryChain(None)),
    )
    resp = client.post("/v1/tokens/buy", json={"accountName": "Missing", "tokens": 5})
    assert resp.status_code == 404


def test_redeem_tokens_success(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")

    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )
    balance_chain = QueryChain({"balance": 20})
    write_chain = QueryChain()

    def table(name):
        if name == "accounts":
            return account_chain
        if name == "token_balances":
            return balance_chain
        return write_chain

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
    )

    resp = client.post("/v1/tokens/redeem", json={"accountName": "Main", "tokens": 6})
    assert resp.status_code == 200
    assert resp.json == {
        "accountName": "Main",
        "tokensRedeemed": 6,
        "tokenBalance": 14,
    }


def test_redeem_tokens_conflict_when_insufficient_balance(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")

    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )
    balance_chain = QueryChain({"balance": 3})

    def table(name):
        return account_chain if name == "accounts" else balance_chain

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
    )
    resp = client.post("/v1/tokens/redeem", json={"accountName": "Main", "tokens": 9})
    assert resp.status_code == 409


def test_redeem_tokens_forbidden_when_not_account_owner(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(
            table=lambda _n: QueryChain(
                {"account_id": "a1", "account_name": "Main", "created_by": "other-user"}
            )
        ),
    )
    resp = client.post("/v1/tokens/redeem", json={"accountName": "Main", "tokens": 4})
    assert resp.status_code == 403


def test_tokens_routes_auth_errors(client, monkeypatch):
    monkeypatch.setattr(
        tokens_routes,
        "require_access_token",
        lambda: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    assert client.get("/v1/tokens", json={"accountName": "Main"}).status_code == 401
    assert (
        client.post(
            "/v1/tokens/buy", json={"accountName": "Main", "tokens": 1}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/v1/tokens/redeem", json={"accountName": "Main", "tokens": 1}
        ).status_code
        == 401
    )
