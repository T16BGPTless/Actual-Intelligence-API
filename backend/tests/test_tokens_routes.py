# """Unit tests for token routes."""

# from types import SimpleNamespace
# from postgrest.exceptions import APIError
# from app.routes import tokens as tokens_routes
# from tests.conftest import QueryChain

# def test_token_helpers_cover_validation():
#     assert tokens_routes._require_positive_tokens({"tokens": "bad"}) is None
#     assert tokens_routes._require_positive_tokens({"tokens": 0}) is None
#     assert tokens_routes._require_positive_tokens({"tokens": "2"}) == 2

# def test_execute_data_helper_handles_none():
#     class Q:
#         def execute(self):
#             return None
#     assert tokens_routes._execute_data(Q(), default={"x": 1}) == {"x": 1}

# def _ok_auth(monkeypatch, user_id="u1"):
#     monkeypatch.setattr(tokens_routes, "require_access_token", lambda: ("tok", None))
#     monkeypatch.setattr(
#         tokens_routes,
#         "require_supabase_user",
#         lambda _t: (SimpleNamespace(id=user_id), None),
#     )

# def test_get_tokens_success(client, monkeypatch):
#     _ok_auth(monkeypatch)
#     account_chain = QueryChain({"account_id": "a1", "account_name": "Main", "created_by": "u1"})
#     balance_chain = QueryChain({"balance": 42})
#     def table(name):
#         return account_chain if name == "accounts" else balance_chain
#     monkeypatch.setattr(tokens_routes, "service_client", lambda: SimpleNamespace(table=table))
#     resp = client.get("/v1/tokens")
#     assert resp.status_code == 200
#     assert resp.json == {"tokenBalance": 42}

# def test_get_tokens_user_validation_error(client, monkeypatch):
#     monkeypatch.setattr(tokens_routes, "require_access_token", lambda: ("tok", None))
#     monkeypatch.setattr(
#         tokens_routes,
#         "require_supabase_user",
#         lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
#     )
#     resp = client.get("/v1/tokens")
#     assert resp.status_code == 401

# def test_get_tokens_not_found(client, monkeypatch):
#     _ok_auth(monkeypatch)
#     monkeypatch.setattr(
#         tokens_routes,
#         "service_client",
#         lambda: SimpleNamespace(table=lambda _n: QueryChain(None)),
#     )
#     resp = client.get("/v1/tokens")
#     assert resp.status_code == 404

# def test_buy_tokens_success(client, monkeypatch):
#     _ok_auth(monkeypatch, user_id="u1")
#     account_chain = QueryChain({"account_id": "a1", "account_name": "Main", "created_by": "u1"})
#     balance_chain = QueryChain({"balance": 10})
#     write_chain = QueryChain()
#     def table(name):
#         if name == "accounts": return account_chain
#         if name == "token_balances": return balance_chain
#         return write_chain
#     monkeypatch.setattr(tokens_routes, "service_client", lambda: SimpleNamespace(table=table))

#     resp = client.post("/v1/tokens/buy", json={"tokens": 5})
#     assert resp.status_code == 200
#     assert resp.json == {"tokensAdded": 5, "tokenBalance": 15}

# def test_buy_tokens_missing_tokens(client, monkeypatch):
#     _ok_auth(monkeypatch)
#     resp = client.post("/v1/tokens/buy", json={})
#     assert resp.status_code == 400

# def test_redeem_tokens_success(client, monkeypatch):
#     _ok_auth(monkeypatch, user_id="u1")
#     account_chain = QueryChain({"account_id": "a1", "account_name": "Main", "created_by": "u1"})
#     balance_chain = QueryChain({"balance": 20})
#     write_chain = QueryChain()
#     def table(name):
#         if name == "accounts": return account_chain
#         if name == "token_balances": return balance_chain
#         return write_chain
#     monkeypatch.setattr(tokens_routes, "service_client", lambda: SimpleNamespace(table=table))

#     resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
#     assert resp.status_code == 200
#     assert resp.json == {"tokensRedeemed": 5, "tokenBalance": 15}

# def test_redeem_tokens_insufficient_balance(client, monkeypatch):
#     _ok_auth(monkeypatch, user_id="u1")
#     account_chain = QueryChain({"account_id": "a1", "account_name": "Main", "created_by": "u1"})
#     balance_chain = QueryChain({"balance": 2})
#     def table(name):
#         return account_chain if name == "accounts" else balance_chain
#     monkeypatch.setattr(tokens_routes, "service_client", lambda: SimpleNamespace(table=table))

#     resp = client.post("/v1/tokens/redeem", json={"tokens": 5})
#     assert resp.status_code == 409
#     assert resp.json["error"] == "CONFLICT"

# def test_redeem_tokens_missing_tokens(client, monkeypatch):
#     _ok_auth(monkeypatch)
#     resp = client.post("/v1/tokens/redeem", json={})
#     assert resp.status_code == 400

