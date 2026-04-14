"""Unit tests for token routes."""

from types import SimpleNamespace

from postgrest.exceptions import APIError

from app.routes import tokens as tokens_routes
from tests.conftest import QueryChain


def test_token_helpers_cover_validation():
    assert tokens_routes._require_account_name({"accountName": " Main "}) == "Main"
    assert tokens_routes._require_account_name({"accountName": ""}) is None
    assert tokens_routes._require_account_name({"accountName": 1}) is None
    assert tokens_routes._require_positive_tokens({"tokens": "bad"}) is None
    assert tokens_routes._require_positive_tokens({"tokens": 0}) is None
    assert tokens_routes._require_positive_tokens({"tokens": "2"}) == 2


def test_execute_data_helper_handles_none():
    class Q:
        def execute(self):
            return None

    assert tokens_routes._execute_data(Q(), default={"x": 1}) == {"x": 1}


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


def test_get_tokens_user_validation_error(client, monkeypatch):
    monkeypatch.setattr(tokens_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        tokens_routes,
        "require_supabase_user",
        lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    resp = client.get("/v1/tokens", json={"accountName": "Main"})
    assert resp.status_code == 401


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


def test_get_tokens_internal_on_balance_lookup_error(client, monkeypatch):
    _ok_auth(monkeypatch)

    class BadBalanceChain(QueryChain):
        def execute(self):
            raise APIError({"message": "boom"})

    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )

    def table(name):
        return account_chain if name == "accounts" else BadBalanceChain()

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
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


def test_buy_tokens_bad_request_and_internal_error(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    assert client.post("/v1/tokens/buy", json={}).status_code == 400

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "boom"})

    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda _n: BadChain()),
    )
    resp = client.post("/v1/tokens/buy", json={"accountName": "Main", "tokens": 1})
    assert resp.status_code == 500


def test_buy_tokens_user_validation_error(client, monkeypatch):
    monkeypatch.setattr(tokens_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        tokens_routes,
        "require_supabase_user",
        lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    resp = client.post("/v1/tokens/buy", json={"accountName": "Main", "tokens": 1})
    assert resp.status_code == 401


def test_buy_tokens_creates_balance_row_when_missing(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )
    no_balance_chain = QueryChain(None)
    write_chain = QueryChain()

    def table(name):
        if name == "accounts":
            return account_chain
        if name == "token_balances":
            return no_balance_chain
        return write_chain

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
    )
    resp = client.post("/v1/tokens/buy", json={"accountName": "Main", "tokens": 3})
    assert resp.status_code == 200
    assert resp.json["tokenBalance"] == 3


def test_buy_tokens_internal_on_write_error(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")

    class BadWriteChain(QueryChain):
        def execute(self):
            raise APIError({"message": "write failed"})

    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )
    balance_chain = QueryChain({"balance": 1})

    def table(name):
        if name == "accounts":
            return account_chain
        if name == "token_balances":
            return balance_chain
        return BadWriteChain()

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
    )
    resp = client.post("/v1/tokens/buy", json={"accountName": "Main", "tokens": 2})
    assert resp.status_code == 500


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


def test_redeem_tokens_user_validation_error(client, monkeypatch):
    monkeypatch.setattr(tokens_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        tokens_routes,
        "require_supabase_user",
        lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    resp = client.post("/v1/tokens/redeem", json={"accountName": "Main", "tokens": 1})
    assert resp.status_code == 401


def test_redeem_tokens_not_found(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda _n: QueryChain(None)),
    )
    resp = client.post(
        "/v1/tokens/redeem", json={"accountName": "Missing", "tokens": 1}
    )
    assert resp.status_code == 404


def test_redeem_tokens_internal_on_balance_lookup_error(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")

    class BadBalanceChain(QueryChain):
        def execute(self):
            raise APIError({"message": "boom"})

    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )

    def table(name):
        return account_chain if name == "accounts" else BadBalanceChain()

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
    )
    resp = client.post("/v1/tokens/redeem", json={"accountName": "Main", "tokens": 1})
    assert resp.status_code == 500


def test_redeem_tokens_bad_request_and_internal_error(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    assert client.post("/v1/tokens/redeem", json={}).status_code == 400

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "boom"})

    monkeypatch.setattr(
        tokens_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda _n: BadChain()),
    )
    resp = client.post("/v1/tokens/redeem", json={"accountName": "Main", "tokens": 1})
    assert resp.status_code == 500


def test_redeem_tokens_internal_on_write_error(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")

    class BadWriteChain(QueryChain):
        def execute(self):
            raise APIError({"message": "write failed"})

    account_chain = QueryChain(
        {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
    )
    balance_chain = QueryChain({"balance": 9})

    def table(name):
        if name == "accounts":
            return account_chain
        if name == "token_balances":
            return balance_chain
        return BadWriteChain()

    monkeypatch.setattr(
        tokens_routes, "service_client", lambda: SimpleNamespace(table=table)
    )
    resp = client.post("/v1/tokens/redeem", json={"accountName": "Main", "tokens": 2})
    assert resp.status_code == 500


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
