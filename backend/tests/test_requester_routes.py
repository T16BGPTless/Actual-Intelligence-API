"""Unit tests for requester routes."""

from http import HTTPStatus
from types import SimpleNamespace
from app.routes import requester as req_routes
from app.routes.helpers import return_error
from postgrest.exceptions import APIError


def _patch_auth(monkeypatch, user_id="user-1"):
    monkeypatch.setattr(req_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        req_routes,
        "require_supabase_user",
        lambda t: (SimpleNamespace(id=user_id), None),
    )
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace())


class FakeChain:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.count = 0
        self.calls = []

    def select(self, *a):
        self.calls.append(("select", a))
        return self

    def eq(self, *a):
        self.calls.append(("eq", a))
        return self

    def maybe_single(self):
        self.calls.append(("maybe_single", ()))
        return self

    def insert(self, *a):
        self.calls.append(("insert", a))
        return self

    def update(self, *a):
        self.calls.append(("update", a))
        return self

    def in_(self, *a):
        self.calls.append(("in_", a))
        return self

    def order(self, *a, **k):
        self.calls.append(("order", (a, k)))
        return self

    def execute(self):
        if self.count >= len(self.responses):
            return SimpleNamespace(data=[])
        res = self.responses[self.count]
        self.count += 1
        if isinstance(res, Exception):
            raise res
        return SimpleNamespace(data=res)


def test_create_chat_all(client, monkeypatch):
    _patch_auth(monkeypatch)
    # Success
    monkeypatch.setattr(
        req_routes,
        "create_chat_with_initial_request",
        lambda *a: ({"chat_id": "c1"}, None),
    )
    monkeypatch.setattr(
        req_routes, "get_chat_or_none", lambda *a: {"chat_id": "c1", "status": "open"}
    )
    monkeypatch.setattr(req_routes, "build_chat_detail", lambda *a: {"chatID": "c1"})
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "test", "tokensToSpend": 10}
    )
    assert resp.status_code == 201
    # Missing fields
    resp = client.post("/v1/requester/chats", json={"requestText": "test"})
    assert resp.status_code == 400
    # Invalid tokens
    monkeypatch.setattr(
        req_routes,
        "create_chat_with_initial_request",
        lambda *a: (None, "invalid_tokens"),
    )
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "test", "tokensToSpend": 10}
    )
    assert resp.status_code == 400
    # Generic error
    monkeypatch.setattr(
        req_routes, "create_chat_with_initial_request", lambda *a: (None, "fail")
    )
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "test", "tokensToSpend": 10}
    )
    assert resp.status_code == 500
    # get_chat_or_none fails
    monkeypatch.setattr(
        req_routes,
        "create_chat_with_initial_request",
        lambda *a: ({"chat_id": "c1"}, None),
    )
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "test", "tokensToSpend": 10}
    )
    assert resp.status_code == 500


def test_get_user_chats_all(client, monkeypatch):
    _patch_auth(monkeypatch)
    # Success
    chain = FakeChain([[{"chat_id": "1"}]])
    monkeypatch.setattr(
        req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: chain)
    )
    monkeypatch.setattr(req_routes, "chat_summary_dict", lambda *a: {"id": "1"})
    resp = client.get(
        "/v1/requester/chats", query_string={"category": "tech", "status": "open"}
    )
    assert resp.status_code == 200
    # Error branch
    chain2 = FakeChain([APIError({"message": "fail"})])
    monkeypatch.setattr(
        req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: chain2)
    )
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 500


def test_get_chat_detail_all(client, monkeypatch):
    _patch_auth(monkeypatch)
    # Success
    monkeypatch.setattr(
        req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1"}
    )
    monkeypatch.setattr(req_routes, "build_chat_detail", lambda *a: {"id": "1"})
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 200
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 404
    monkeypatch.setattr(
        req_routes, "get_chat_or_none", lambda *a: {"requester_id": "other"}
    )
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 403


def test_post_message_full(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "message_dict", lambda m: m)

    # 1. SUCCESS (Paid)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed", "tokens_spent": 10},
    )
    responses_ok = [
        {"account_id": "a1"},  # account lookup
        {"balance": 100},  # balance select
        [{"id": "b1"}],  # balance update
        [{"id": "tx1"}],  # tx insert
        [{"id": "msg-1"}],  # message insert
        [{"id": "chat-up"}],  # chat update
    ]
    chain_ok = FakeChain(responses_ok)
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_ok)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10}
    )
    assert resp.status_code == 201

    # 2. SUCCESS (Free)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )
    chain_f = FakeChain([[{"id": "m-free"}]])
    monkeypatch.setattr(
        req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: chain_f)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0}
    )
    assert resp.status_code == 201


def test_post_message_errors_and_edge_cases(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "message_dict", lambda m: m)

    # Missing fields
    resp = client.post("/v1/requester/chats/1/messages", json={})
    assert resp.status_code == 400

    # Chat not found (Line 120)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi"})
    assert resp.status_code == 404

    # Forbidden (Line 122)
    monkeypatch.setattr(
        req_routes, "get_chat_or_none", lambda *a: {"requester_id": "other"}
    )
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi"})
    assert resp.status_code == 403

    # Not claimed (Line 124)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "open"},
    )
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi"})
    assert resp.status_code == 400

    # Invalid tokens type (Line 128)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": -1}
    )
    assert resp.status_code == 400

    # Free Path: Insert fail (Line 142)
    chain_f1 = FakeChain([[]])
    monkeypatch.setattr(
        req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: chain_f1)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0}
    )
    assert resp.status_code == 500

    # Free Path: Exception (Line 145)
    chain_f2 = FakeChain([Exception("crash free")])
    monkeypatch.setattr(
        req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: chain_f2)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0}
    )
    assert resp.status_code == 500

    # Paid Path: Account not found (Line 152)
    chain_p1 = FakeChain([None])
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_p1)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10}
    )
    assert resp.status_code == 404

    # Paid Path: Insufficient balance (Line 158)
    chain_p2 = FakeChain([{"account_id": "a1"}, {"balance": 5}])
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_p2)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10}
    )
    assert resp.status_code == 400

    # Paid Path: Message creation fail (Line 182)
    responses_p3 = [
        {"account_id": "a1"},
        {"balance": 100},
        [{"id": "b1"}],
        [{"id": "tx1"}],
        [],
    ]
    chain_p3 = FakeChain(responses_p3)
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_p3)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10}
    )
    assert resp.status_code == 500

    # Paid Path: APIError insufficient (Line 195)
    chain_p4 = FakeChain(
        [{"account_id": "a1"}, APIError({"message": "insufficient tokens"})]
    )
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_p4)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10}
    )
    assert resp.status_code == 400

    # Paid Path: APIError generic (Line 196)
    chain_p5 = FakeChain(
        [{"account_id": "a1"}, APIError({"message": "other db error"})]
    )
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_p5)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10}
    )
    assert resp.status_code == 500

    # Paid Path: Exception (Line 198)
    chain_p6 = FakeChain([Exception("crash paid")])
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_p6)
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10}
    )
    assert resp.status_code == 500


def test_review_chat_logic_and_edge_cases(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "build_chat_detail", lambda *a, **k: {"id": "c1"})

    # 1. SUCCESS with Payout (Line 236-252, 265)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {
            "requester_id": "user-1",
            "status": "closing",
            "responder_id": "res-1",
            "tokens_spent": 50,
        },
    )
    responses_r_ok = [
        {"account_id": "acc-res"},  # responder account lookup
        [{"id": "tx-pay"}],  # responder tx insert
        {"balance": 0},  # responder balance check
        [{"id": "bal-up"}],  # responder balance update
        [{"id": "chat-closed"}],  # chat update (review/close)
    ]
    chain_ok = FakeChain(responses_r_ok)
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_ok)
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 200

    # 2. Validation Errors
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5}
    )  # Missing resolved
    assert resp.status_code == 400
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 6, "resolved": True}
    )  # Invalid rating
    assert resp.status_code == 400
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": "yes"}
    )  # Invalid resolved type
    assert resp.status_code == 400

    # 3. Not Found / Forbidden / Invalid State (Line 226, 228, 230)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 404

    monkeypatch.setattr(
        req_routes, "get_chat_or_none", lambda *a: {"requester_id": "other"}
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 403

    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "open"},
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 400

    # 4. Update failed (Line 263)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "closing"},
    )
    chain_r1 = FakeChain([[]])
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_r1)
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 500

    # 5. Exception (Line 267)
    chain_r2 = FakeChain([Exception("crash review")])
    monkeypatch.setattr(
        req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain_r2)
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 500


def test_auth_failures_all_lines(client, monkeypatch):
    endpoints = [
        ("POST", "/v1/requester/chats", {}),
        ("GET", "/v1/requester/chats", None),
        ("GET", "/v1/requester/chats/1", None),
        ("POST", "/v1/requester/chats/1/messages", {"message": "hi"}),
        ("POST", "/v1/requester/chats/1/review", {"rating": 5, "resolved": True}),
    ]
    for method, path, body in endpoints:
        monkeypatch.setattr(
            req_routes, "require_access_token", lambda: (None, ({"err": "1"}, 401))
        )
        if method == "POST":
            resp = client.post(path, json=body)
        else:
            resp = client.get(path)
        assert resp.status_code == 401

        monkeypatch.setattr(req_routes, "require_access_token", lambda: ("tok", None))
        monkeypatch.setattr(
            req_routes, "require_supabase_user", lambda t: (None, ({"err": "2"}, 401))
        )
        if method == "POST":
            resp = client.post(path, json=body)
        else:
            resp = client.get(path)
        assert resp.status_code == 401
