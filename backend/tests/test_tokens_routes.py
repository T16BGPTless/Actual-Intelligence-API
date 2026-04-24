"""Unit tests for token routes."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from app.routes import tokens as tokens_routes
from tests.conftest import QueryChain


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_user(user_id="u1", email="user@example.com", name="Test User"):
    return SimpleNamespace(
        id=user_id,
        email=email,
        user_metadata={"name": name},
    )


def _ok_auth(monkeypatch, user=None):
    """Patch require_access_token + require_supabase_user to succeed."""
    if user is None:
        user = _fake_user()
    monkeypatch.setattr(tokens_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        tokens_routes,
        "require_supabase_user",
        lambda _t: (user, None),
    )


def _make_client(account_data=None, balance_data=None):
    """
    Build a fake service_client whose .table() dispatch returns appropriate
    QueryChain objects for 'accounts' and 'token_balances' tables, and a
    write-only chain for everything else.
    """
    account_row = account_data  # e.g. {"account_id": "a1", ...} or None
    balance_row = balance_data  # e.g. {"balance": 42} or None

    # Wrap scalar row in a list as the route does .execute().data which is a list
    accounts_chain = QueryChain([account_row] if account_row else [])
    balances_chain = QueryChain([balance_row] if balance_row else [])
    write_chain = QueryChain(None)

    def table(name):
        if name == "accounts":
            return accounts_chain
        if name == "token_balances":
            return balances_chain
        return write_chain

    return SimpleNamespace(table=table)


# ---------------------------------------------------------------------------
# _require_positive_tokens
# ---------------------------------------------------------------------------


class TestRequirePositiveTokens:
    def test_none_value_returns_none(self):
        assert tokens_routes._require_positive_tokens({}) is None

    def test_string_non_numeric_returns_none(self):
        assert tokens_routes._require_positive_tokens({"tokens": "bad"}) is None

    def test_zero_returns_none(self):
        assert tokens_routes._require_positive_tokens({"tokens": 0}) is None

    def test_negative_returns_none(self):
        assert tokens_routes._require_positive_tokens({"tokens": -5}) is None

    def test_positive_int_returns_value(self):
        assert tokens_routes._require_positive_tokens({"tokens": 5}) == 5

    def test_positive_string_int_returns_value(self):
        assert tokens_routes._require_positive_tokens({"tokens": "10"}) == 10

    def test_float_string_returns_none(self):
        # int("3.5") raises ValueError - should return None
        assert tokens_routes._require_positive_tokens({"tokens": "3.5"}) is None


# ---------------------------------------------------------------------------
# _execute_data
# ---------------------------------------------------------------------------


class TestExecuteData:
    def test_returns_data_from_result(self):
        chain = QueryChain({"key": "val"})
        assert tokens_routes._execute_data(chain) == {"key": "val"}

    def test_returns_default_when_result_is_none(self):
        class NullQuery:
            def execute(self):
                return None

        result = tokens_routes._execute_data(NullQuery(), default={"x": 1})
        assert result == {"x": 1}

    def test_default_is_none_when_not_specified(self):
        class NullQuery:
            def execute(self):
                return None

        assert tokens_routes._execute_data(NullQuery()) is None


# ---------------------------------------------------------------------------
# _account_for_user
# ---------------------------------------------------------------------------


class TestAccountForUser:
    def test_returns_first_row(self):
        row = {"account_id": "a1", "account_name": "Main", "created_by": "u1"}
        chain = QueryChain([row])
        client = SimpleNamespace(table=lambda _n: chain)
        result = tokens_routes._account_for_user(client, "u1")
        assert result == row

    def test_returns_none_when_empty(self):
        chain = QueryChain([])
        client = SimpleNamespace(table=lambda _n: chain)
        result = tokens_routes._account_for_user(client, "u1")
        assert result is None

    def test_returns_none_when_data_is_none(self):
        chain = QueryChain(None)
        client = SimpleNamespace(table=lambda _n: chain)
        result = tokens_routes._account_for_user(client, "u1")
        assert result is None


# ---------------------------------------------------------------------------
# _send_invoice
# ---------------------------------------------------------------------------


class TestSendInvoice:
    def test_sends_invoice_and_notify_on_success(self):
        """Checks that both requests.post calls are made when an invoice ID is found."""
        post_calls = []

        class FakeResp:
            text = "<cbc:ID>12345</cbc:ID>"

        def fake_post(url, json=None, headers=None, timeout=None):
            post_calls.append(url)
            return FakeResp()

        with patch("app.routes.tokens.requests.post", side_effect=fake_post):
            tokens_routes._send_invoice(
                "Customer", "c@example.com", 10, 5.0, "api-key", 10
            )

        assert len(post_calls) == 2
        assert "generate" in post_calls[0]
        assert "notify" in post_calls[1]
        assert "12345" in post_calls[1]

    def test_no_notify_when_no_invoice_id_found(self):
        """If regex finds no ID, only the generate call is made."""
        post_calls = []

        class FakeResp:
            text = "no id here"

        def fake_post(url, json=None, headers=None, timeout=None):
            post_calls.append(url)
            return FakeResp()

        with patch("app.routes.tokens.requests.post", side_effect=fake_post):
            tokens_routes._send_invoice(
                "Customer", "c@example.com", 10, 5.0, "api-key", 10
            )

        assert len(post_calls) == 1

    def test_swallows_request_exceptions(self):
        """Invoice errors must not propagate to callers."""

        def raise_error(*_a, **_k):
            raise Exception("network failure")

        with patch("app.routes.tokens.requests.post", side_effect=raise_error):
            # Should NOT raise
            tokens_routes._send_invoice(
                "Customer", "c@example.com", 10, 5.0, "api-key", 10
            )


# ---------------------------------------------------------------------------
# GET /v1/tokens
# ---------------------------------------------------------------------------


class TestGetTokens:
    def test_returns_token_balance(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 42},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.get("/v1/tokens")
        assert resp.status_code == 200
        assert resp.json["tokenBalance"] == 42

    def test_returns_zero_balance_when_no_balance_row(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data=None,
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.get("/v1/tokens")
        assert resp.status_code == 200
        assert resp.json["tokenBalance"] == 0

    def test_returns_zero_when_balance_is_null(self, client, monkeypatch):
        """balance column can be NULL – should fall back to 0."""
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": None},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.get("/v1/tokens")
        assert resp.status_code == 200
        assert resp.json["tokenBalance"] == 0

    def test_401_when_no_auth_token(self, client, monkeypatch):
        monkeypatch.setattr(
            tokens_routes,
            "require_access_token",
            lambda: (None, ({"error": "UNAUTHORIZED"}, 401)),
        )
        resp = client.get("/v1/tokens")
        assert resp.status_code == 401

    def test_401_when_user_lookup_fails(self, client, monkeypatch):
        monkeypatch.setattr(
            tokens_routes, "require_access_token", lambda: ("tok", None)
        )
        monkeypatch.setattr(
            tokens_routes,
            "require_supabase_user",
            lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
        )
        resp = client.get("/v1/tokens")
        assert resp.status_code == 401

    def test_404_when_account_not_found(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(account_data=None, balance_data=None)
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.get("/v1/tokens")
        assert resp.status_code == 404
        assert resp.json["error"] == "NOT_FOUND"

    def test_500_on_account_api_error(self, client, monkeypatch):
        _ok_auth(monkeypatch)

        def bad_table(_n):
            chain = QueryChain(None)
            chain.execute = lambda: (_ for _ in ()).throw(
                APIError({"message": "db error"})
            )
            return chain

        monkeypatch.setattr(
            tokens_routes,
            "service_client",
            lambda: SimpleNamespace(table=bad_table),
        )
        resp = client.get("/v1/tokens")
        assert resp.status_code == 500
        assert resp.json["error"] == "INTERNAL_SERVER_ERROR"

    def test_500_on_balance_api_error(self, client, monkeypatch):
        _ok_auth(monkeypatch)

        call_count = [0]

        def mixed_table(name):
            if name == "accounts":
                return QueryChain(
                    [{"account_id": "a1", "account_name": "Main", "created_by": "u1"}]
                )

            # Raise on token_balances query
            class ErrChain(QueryChain):
                def execute(self):
                    raise APIError({"message": "balance error"})

            return ErrChain()

        monkeypatch.setattr(
            tokens_routes,
            "service_client",
            lambda: SimpleNamespace(table=mixed_table),
        )
        resp = client.get("/v1/tokens")
        assert resp.status_code == 500
        assert resp.json["error"] == "INTERNAL_SERVER_ERROR"


# ---------------------------------------------------------------------------
# POST /v1/tokens/buy
# ---------------------------------------------------------------------------


class TestBuyTokens:
    def test_buy_updates_existing_balance(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 10},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)
        monkeypatch.setattr(tokens_routes, "_send_invoice", lambda *_a, **_k: None)

        resp = client.post("/v1/tokens/buy", json={"tokens": 5, "cost": 2.50})
        assert resp.status_code == 200
        assert resp.json["tokensAdded"] == 5
        assert resp.json["tokenBalance"] == 15
        assert resp.json["cost"] == 2.50

    def test_buy_inserts_when_no_existing_balance(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data=None,
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)
        monkeypatch.setattr(tokens_routes, "_send_invoice", lambda *_a, **_k: None)

        resp = client.post("/v1/tokens/buy", json={"tokens": 20, "cost": 10.0})
        assert resp.status_code == 200
        assert resp.json["tokensAdded"] == 20
        assert resp.json["tokenBalance"] == 20

    def test_buy_triggers_invoice(self, client, monkeypatch):
        user = _fake_user(name="John Doe", email="john@example.com")
        _ok_auth(monkeypatch, user=user)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 0},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        invoice_calls = []
        monkeypatch.setattr(
            tokens_routes,
            "_send_invoice",
            lambda *args, **kwargs: invoice_calls.append(args),
        )

        monkeypatch.setenv("INVOICE_API_TOKEN", "test-invoice-token")
        client.post("/v1/tokens/buy", json={"tokens": 3, "cost": 1.50})

        assert len(invoice_calls) == 1
        name, email, tokens, cost, api_token, gst = invoice_calls[0]
        assert name == "John Doe"
        assert email == "john@example.com"
        assert tokens == 3
        assert cost == 1.50

    def test_buy_falls_back_to_email_when_name_missing(self, client, monkeypatch):
        user = SimpleNamespace(
            id="u1", email="fallback@example.com", user_metadata={"role": "member"}
        )
        _ok_auth(monkeypatch, user=user)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 0},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        invoice_calls = []
        monkeypatch.setattr(
            tokens_routes,
            "_send_invoice",
            lambda *args, **kwargs: invoice_calls.append(args),
        )
        client.post("/v1/tokens/buy", json={"tokens": 1, "cost": 0.50})

        name = invoice_calls[0][0]
        assert name == "fallback@example.com"

    def test_buy_uses_customer_default_when_no_user_metadata(self, client, monkeypatch):
        user = SimpleNamespace(id="u1", email="no-meta@example.com", user_metadata=None)
        _ok_auth(monkeypatch, user=user)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 0},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        invoice_calls = []
        monkeypatch.setattr(
            tokens_routes,
            "_send_invoice",
            lambda *args, **kwargs: invoice_calls.append(args),
        )
        client.post("/v1/tokens/buy", json={"tokens": 1, "cost": 0.50})

        name = invoice_calls[0][0]
        assert name == "Customer"

    def test_400_when_tokens_missing(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/buy", json={"cost": 1.0})
        assert resp.status_code == 400
        assert resp.json["error"] == "BAD_REQUEST"

    def test_400_when_tokens_zero(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/buy", json={"tokens": 0, "cost": 1.0})
        assert resp.status_code == 400

    def test_400_when_tokens_negative(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/buy", json={"tokens": -1, "cost": 1.0})
        assert resp.status_code == 400

    def test_400_when_tokens_non_numeric(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/buy", json={"tokens": "many", "cost": 1.0})
        assert resp.status_code == 400

    def test_400_when_cost_missing(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/buy", json={"tokens": 5})
        assert resp.status_code == 400
        assert resp.json["error"] == "BAD_REQUEST"

    def test_400_when_body_is_empty(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/buy", json={})
        assert resp.status_code == 400

    def test_400_when_no_body(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/buy")
        assert resp.status_code == 400

    def test_401_when_no_auth_token(self, client, monkeypatch):
        monkeypatch.setattr(
            tokens_routes,
            "require_access_token",
            lambda: (None, ({"error": "UNAUTHORIZED"}, 401)),
        )
        resp = client.post("/v1/tokens/buy", json={"tokens": 5, "cost": 1.0})
        assert resp.status_code == 401

    def test_401_when_user_lookup_fails(self, client, monkeypatch):
        monkeypatch.setattr(
            tokens_routes, "require_access_token", lambda: ("tok", None)
        )
        monkeypatch.setattr(
            tokens_routes,
            "require_supabase_user",
            lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
        )
        resp = client.post("/v1/tokens/buy", json={"tokens": 5, "cost": 1.0})
        assert resp.status_code == 401

    def test_404_when_account_not_found(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(account_data=None, balance_data=None)
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.post("/v1/tokens/buy", json={"tokens": 5, "cost": 1.0})
        assert resp.status_code == 404
        assert resp.json["error"] == "NOT_FOUND"

    def test_500_on_account_api_error(self, client, monkeypatch):
        _ok_auth(monkeypatch)

        def bad_table(_n):
            class ErrChain(QueryChain):
                def execute(self):
                    raise APIError({"message": "db error"})

            return ErrChain()

        monkeypatch.setattr(
            tokens_routes,
            "service_client",
            lambda: SimpleNamespace(table=bad_table),
        )
        resp = client.post("/v1/tokens/buy", json={"tokens": 5, "cost": 1.0})
        assert resp.status_code == 500

    def test_500_on_balance_api_error(self, client, monkeypatch):
        _ok_auth(monkeypatch)

        def mixed_table(name):
            if name == "accounts":
                return QueryChain(
                    [{"account_id": "a1", "account_name": "Main", "created_by": "u1"}]
                )

            class ErrChain(QueryChain):
                def execute(self):
                    raise APIError({"message": "balance error"})

            return ErrChain()

        monkeypatch.setattr(
            tokens_routes,
            "service_client",
            lambda: SimpleNamespace(table=mixed_table),
        )
        resp = client.post("/v1/tokens/buy", json={"tokens": 5, "cost": 1.0})
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# POST /v1/tokens/redeem
# ---------------------------------------------------------------------------


class TestRedeemTokens:
    def test_redeem_success_reduces_balance(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 20},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 200
        assert resp.json["tokensRedeemed"] == 5
        assert resp.json["tokenBalance"] == 15

    def test_redeem_exact_balance_succeeds(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 5},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 200
        assert resp.json["tokenBalance"] == 0

    def test_409_when_insufficient_balance(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 2},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 409
        assert resp.json["error"] == "CONFLICT"

    def test_409_when_zero_balance(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data={"balance": 0},
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.post("/v1/tokens/redeem", json={"tokens": 1})
        assert resp.status_code == 409

    def test_409_when_no_balance_row_exists(self, client, monkeypatch):
        """No balance row means balance=0, any redeem amount should conflict."""
        _ok_auth(monkeypatch)
        fake_client = _make_client(
            account_data={
                "account_id": "a1",
                "account_name": "Main",
                "created_by": "u1",
            },
            balance_data=None,
        )
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.post("/v1/tokens/redeem", json={"tokens": 1})
        assert resp.status_code == 409

    def test_400_when_tokens_missing(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/redeem", json={})
        assert resp.status_code == 400
        assert resp.json["error"] == "BAD_REQUEST"

    def test_400_when_tokens_zero(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/redeem", json={"tokens": 0})
        assert resp.status_code == 400

    def test_400_when_tokens_negative(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/redeem", json={"tokens": -3})
        assert resp.status_code == 400

    def test_400_when_tokens_non_numeric(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/redeem", json={"tokens": "lots"})
        assert resp.status_code == 400

    def test_400_when_no_body(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        resp = client.post("/v1/tokens/redeem")
        assert resp.status_code == 400

    def test_401_when_no_auth_token(self, client, monkeypatch):
        monkeypatch.setattr(
            tokens_routes,
            "require_access_token",
            lambda: (None, ({"error": "UNAUTHORIZED"}, 401)),
        )
        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 401

    def test_401_when_user_lookup_fails(self, client, monkeypatch):
        monkeypatch.setattr(
            tokens_routes, "require_access_token", lambda: ("tok", None)
        )
        monkeypatch.setattr(
            tokens_routes,
            "require_supabase_user",
            lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
        )
        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 401

    def test_404_when_account_not_found(self, client, monkeypatch):
        _ok_auth(monkeypatch)
        fake_client = _make_client(account_data=None, balance_data=None)
        monkeypatch.setattr(tokens_routes, "service_client", lambda: fake_client)

        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 404
        assert resp.json["error"] == "NOT_FOUND"

    def test_500_on_account_api_error(self, client, monkeypatch):
        _ok_auth(monkeypatch)

        def bad_table(_n):
            class ErrChain(QueryChain):
                def execute(self):
                    raise APIError({"message": "db error"})

            return ErrChain()

        monkeypatch.setattr(
            tokens_routes,
            "service_client",
            lambda: SimpleNamespace(table=bad_table),
        )
        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 500

    def test_500_on_balance_api_error(self, client, monkeypatch):
        _ok_auth(monkeypatch)

        def mixed_table(name):
            if name == "accounts":
                return QueryChain(
                    [{"account_id": "a1", "account_name": "Main", "created_by": "u1"}]
                )

            class ErrChain(QueryChain):
                def execute(self):
                    raise APIError({"message": "balance error"})

            return ErrChain()

        monkeypatch.setattr(
            tokens_routes,
            "service_client",
            lambda: SimpleNamespace(table=mixed_table),
        )
        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 500

    def test_500_on_update_api_error(self, client, monkeypatch):
        """APIError raised during the UPDATE/INSERT write phase returns 500."""
        _ok_auth(monkeypatch)

        class UpdatingErrChain(QueryChain):
            def update(self, *_a, **_k):
                class Inner(QueryChain):
                    def execute(self):
                        raise APIError({"message": "write error"})

                return Inner()

        def mixed_table(name):
            if name == "accounts":
                return QueryChain(
                    [{"account_id": "a1", "account_name": "Main", "created_by": "u1"}]
                )
            return UpdatingErrChain([{"balance": 100}])

        monkeypatch.setattr(
            tokens_routes,
            "service_client",
            lambda: SimpleNamespace(table=mixed_table),
        )
        resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
        assert resp.status_code == 500
