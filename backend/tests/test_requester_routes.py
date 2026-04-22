"""Unit tests for requester routes."""

from http import HTTPStatus
from types import SimpleNamespace
from app.routes import requester as req_routes
from app.routes.helpers import return_error
from postgrest.exceptions import APIError


def _patch_auth(monkeypatch):
    monkeypatch.setattr(req_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        req_routes,
        "require_supabase_user",
        lambda t: (SimpleNamespace(id="user-1"), None),
    )
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace())

    class FakeServiceTable:
        def select(self, *a):
            return self

        def eq(self, *a):
            return self

        def maybe_single(self):
            return self

        def in_(self, *a):
            return self

        def execute(self):
            return SimpleNamespace(data={"account_id": "acc-1", "balance": 1000})

        def update(self, *a):
            return self

        def insert(self, *a):
            return self

    monkeypatch.setattr(
        req_routes,
        "service_client",
        lambda *a: SimpleNamespace(table=lambda *a: FakeServiceTable()),
    )


def test_create_chat_missing_fields(client, monkeypatch):
    _patch_auth(monkeypatch)
    resp = client.post("/v1/requester/chats", json={"requestText": "Test"})
    assert resp.status_code == 400
    assert resp.json["error"] == "BAD_REQUEST"


def test_create_chat_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "create_chat_with_initial_request",
        lambda *a: ({"chat_id": "test-id"}, None),
    )

    # 500 error if get_chat_or_none fails
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "test", "tokensToSpend": 5}
    )
    assert resp.status_code == 500

    # success branch
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"chat_id": "test-id", "status": "open"},
    )
    monkeypatch.setattr(
        req_routes,
        "build_chat_detail",
        lambda *a: {"chatID": "test-id", "status": "open"},
    )
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "test", "tokensToSpend": 5}
    )
    assert resp.status_code == 201
    assert resp.json["chatID"] == "test-id"


def test_get_user_chats(client, monkeypatch):
    _patch_auth(monkeypatch)

    class FakeQ:
        def select(self, *a):
            return self

        def eq(self, *a):
            return self

        def in_(self, *a):
            return self

        def order(self, *a, **k):
            return self

        def execute(self):
            return SimpleNamespace(data=[{"chat_id": "1", "status": "open"}])

    monkeypatch.setattr(
        req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeQ())
    )
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 200
    assert len(resp.json) == 1


def test_get_chat_detail_forbidden(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes, "get_chat_or_none", lambda *a: {"requester_id": "other-user"}
    )
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 403


def test_post_message_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )

    class FakeChain:
        def __init__(self, data=None):
            self.data = data or []
            self.calls = []
            self._maybe_single = False

        def select(self, *a):
            self.calls.append(("select", a))
            return self

        def eq(self, *a):
            self.calls.append(("eq", a))
            return self

        def maybe_single(self):
            self.calls.append(("maybe_single", ()))
            self._maybe_single = True
            return self

        def insert(self, *a):
            self.calls.append(("insert", a))
            return self

        def execute(self):
            d = self.data
            if self._maybe_single:
                d = d[0] if d else None
            return SimpleNamespace(data=d)

    acc_chain = FakeChain([{"account_id": "acc-1"}])
    tx_chain = FakeChain([{"tokens": 1}])
    msg_chain = FakeChain([{
        "id": "m1",
        "sender_id": "user-1",
        "sender_type": "requester",
        "message": "hello",
        "tokens": 1,
        "created_at": "2026-04-16T12:00:00+00:00"
    }])

    def table_mock(name):
        if name == "accounts": return acc_chain
        if name == "token_transactions": return tx_chain
        if name == "messages": return msg_chain
        return FakeChain()

    monkeypatch.setattr(req_routes, "service_client", lambda: SimpleNamespace(table=table_mock))
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=table_mock))

    # Test paid message
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hello", "tokensToSpend": 1}
    )
    assert resp.status_code == 201

    # Test free message
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hello", "tokensToSpend": 0}
    )
    assert resp.status_code == 201


def test_review_chat_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "closing"},
    )

    class FakeTable:
        def update(self, *a):
            return self

        def eq(self, *a):
            return self

        def execute(self):
            pass

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(table=lambda *a: FakeTable()),
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 200


def test_auth_failures(client, monkeypatch):
    monkeypatch.setattr(
        req_routes, "require_access_token", lambda: (None, return_error("UNAUTHORIZED"))
    )
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 401

    monkeypatch.setattr(req_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        req_routes,
        "require_supabase_user",
        lambda t: (None, return_error("UNAUTHORIZED")),
    )
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 401


def test_api_error_handling(client, monkeypatch):
    _patch_auth(monkeypatch)

    class FakeErrorQ:
        def select(self, *a):
            return self

        def eq(self, *a):
            return self

        def in_(self, *a):
            return self

        def order(self, *a, **k):
            return self

        def execute(self):
            raise APIError({"message": "db error"})

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(table=lambda *a: FakeErrorQ()),
    )
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 500


def test_get_chat_detail_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 404

    monkeypatch.setattr(
        req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1"}
    )
    monkeypatch.setattr(req_routes, "build_chat_detail", lambda *a: {"id": "1"})
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 200


def test_post_message_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
    resp = client.post("/v1/requester/chats/1/messages", json={})
    assert resp.status_code == 400

    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "x"})
    assert resp.status_code == 404

    monkeypatch.setattr(
        req_routes, "get_chat_or_none", lambda *a: {"requester_id": "other"}
    )
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "x"})
    assert resp.status_code == 403

    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "closed"},
    )
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "x"})
    assert resp.status_code == 400

    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )
    # Test invalid tokens types
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "x", "tokensToSpend": "5"}
    )
    assert resp.status_code == 400
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "x", "tokensToSpend": -2}
    )
    assert resp.status_code == 400

    class FakeTableErr:
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def insert(self, *a): return self
        def execute(self):
            raise APIError({"message": "db error"})

    monkeypatch.setattr(
        req_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda *a: FakeTableErr()),
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "M", "tokensToSpend": 10}
    )
    assert resp.status_code == 500

    class FakeTableErrTokens:
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def insert(self, *a): return self
        def execute(self):
            raise APIError({"message": "invalid_tokens"})

    monkeypatch.setattr(
        req_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda *a: FakeTableErrTokens()),
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "M", "tokensToSpend": 10}
    )
    assert resp.status_code == 400


def test_review_chat_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
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
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 400

    resp = client.post("/v1/requester/chats/1/review", json={})
    assert resp.status_code == 400

    resp = client.post("/v1/requester/chats/1/review", json={"resolved": True})
    assert resp.status_code == 400

    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5})
    assert resp.status_code == 400

    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 6, "resolved": True}
    )
    assert resp.status_code == 400

    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": "5", "resolved": True}
    )
    assert resp.status_code == 400

    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": "yes"}
    )
    assert resp.status_code == 400

    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "closing"},
    )

    class FakeTableErr:
        def update(self, *a):
            return self

        def eq(self, *a):
            return self

        def execute(self):
            raise APIError({"message": "db"})

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(table=lambda *a: FakeTableErr()),
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 5, "resolved": True}
    )
    assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Per-endpoint auth failures (lines 25, 28, 40, 42, 68, 70, 85, 88, 173, 176)
# ---------------------------------------------------------------------------

def _patch_auth_fail_token(monkeypatch):
    from app.routes.helpers import return_error
    monkeypatch.setattr(
        req_routes, "require_access_token", lambda: (None, return_error("UNAUTHORIZED"))
    )


def _patch_auth_fail_user(monkeypatch):
    from app.routes.helpers import return_error
    monkeypatch.setattr(req_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        req_routes,
        "require_supabase_user",
        lambda t: (None, return_error("UNAUTHORIZED")),
    )


def test_create_chat_auth_token_failure(client, monkeypatch):
    _patch_auth_fail_token(monkeypatch)
    resp = client.post("/v1/requester/chats", json={"requestText": "x", "tokensToSpend": 1})
    assert resp.status_code == 401


def test_create_chat_auth_user_failure(client, monkeypatch):
    _patch_auth_fail_user(monkeypatch)
    resp = client.post("/v1/requester/chats", json={"requestText": "x", "tokensToSpend": 1})
    assert resp.status_code == 401


def test_create_chat_invalid_tokens_error(client, monkeypatch):
    """create_chat_with_initial_request returning invalid_tokens → 400."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "create_chat_with_initial_request",
        lambda *a: (None, "invalid_tokens"),
    )
    resp = client.post("/v1/requester/chats", json={"requestText": "x", "tokensToSpend": 0})
    assert resp.status_code == 400
    assert resp.json["error"] == "BAD_REQUEST"


def test_get_user_chats_auth_token_failure(client, monkeypatch):
    _patch_auth_fail_token(monkeypatch)
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 401


def test_get_user_chats_auth_user_failure(client, monkeypatch):
    _patch_auth_fail_user(monkeypatch)
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 401


def test_get_user_chats_with_category_and_status_filters(client, monkeypatch):
    """Exercises the cats and status filter branches in get_user_chats."""
    _patch_auth(monkeypatch)

    class FakeQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def in_(self, *a): return self
        def order(self, *a, **k): return self
        def execute(self): return SimpleNamespace(data=[])

    monkeypatch.setattr(
        req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeQ())
    )
    resp = client.get("/v1/requester/chats?category=tech&status=open")
    assert resp.status_code == 200


def test_get_chat_detail_auth_token_failure(client, monkeypatch):
    _patch_auth_fail_token(monkeypatch)
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 401


def test_get_chat_detail_auth_user_failure(client, monkeypatch):
    _patch_auth_fail_user(monkeypatch)
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 401


def test_post_message_auth_token_failure(client, monkeypatch):
    _patch_auth_fail_token(monkeypatch)
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi"})
    assert resp.status_code == 401


def test_post_message_auth_user_failure(client, monkeypatch):
    _patch_auth_fail_user(monkeypatch)
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi"})
    assert resp.status_code == 401


def test_review_chat_auth_token_failure(client, monkeypatch):
    _patch_auth_fail_token(monkeypatch)
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5, "resolved": True})
    assert resp.status_code == 401


def test_review_chat_auth_user_failure(client, monkeypatch):
    _patch_auth_fail_user(monkeypatch)
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5, "resolved": True})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# review_chat payout path (lines 209-233)
# ---------------------------------------------------------------------------

def test_review_chat_pays_out_responder_tokens(client, monkeypatch):
    """Exercises the full payout path: responder_id set, tokens_spent > 0."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {
            "requester_id": "user-1",
            "status": "closing",
            "responder_id": "resp-1",
            "tokens_spent": 10,
        },
    )

    executed = []

    class FakeTable:
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def update(self, *a): return self
        def insert(self, *a): return self
        def execute(self):
            executed.append(True)
            return SimpleNamespace(data={"account_id": "acc-1", "balance": 50})

    monkeypatch.setattr(
        req_routes,
        "service_client",
        lambda: SimpleNamespace(table=lambda *a: FakeTable()),
    )

    class FakeUserTable:
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): return SimpleNamespace(data=None)

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(table=lambda *a: FakeUserTable()),
    )

    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 4, "resolved": False}
    )
    assert resp.status_code == 200
    assert len(executed) > 0


def test_review_chat_skips_payout_when_no_responder(client, monkeypatch):
    """No responder_id → skip payout block entirely."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {
            "requester_id": "user-1",
            "status": "closing",
            "responder_id": None,
            "tokens_spent": 10,
        },
    )

    class FakeTable:
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): return SimpleNamespace(data=None)

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(table=lambda *a: FakeTable()),
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 3, "resolved": True}
    )
    assert resp.status_code == 200


def test_review_chat_skips_payout_when_zero_tokens(client, monkeypatch):
    """tokens_spent == 0 → skip payout block."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {
            "requester_id": "user-1",
            "status": "closing",
            "responder_id": "resp-1",
            "tokens_spent": 0,
        },
    )

    class FakeTable:
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): return SimpleNamespace(data=None)

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(table=lambda *a: FakeTable()),
    )
    resp = client.post(
        "/v1/requester/chats/1/review", json={"rating": 3, "resolved": True}
    )
    assert resp.status_code == 200



# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Coverage Improvement Tests
# ---------------------------------------------------------------------------

def test_create_chat_generic_error(client, monkeypatch):
    """create_chat returns generic error (err != 'invalid_tokens') → 500."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "create_chat_with_initial_request", lambda *a: (None, "some_db_error"))
    resp = client.post("/v1/requester/chats", json={"requestText": "hi", "tokensToSpend": 10})
    assert resp.status_code == 500
    assert resp.json["message"] == "Unable to create chat"


def test_post_message_free_no_data(client, monkeypatch):
    """Fast path (0 tokens) insert returns no data → 500."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    
    class FakeEmptyTable:
        def insert(self, *a): return self
        def execute(self): return SimpleNamespace(data=[]) # Empty list
    
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeEmptyTable()))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0})
    assert resp.status_code == 500
    assert "Message insert failed" in resp.json["message"]


def test_post_message_free_exception(client, monkeypatch):
    """Fast path (0 tokens) throws general exception → 500."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    
    class FakeCrashTable:
        def insert(self, *a): raise Exception("Unexpected crash")
    
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeCrashTable()))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0})
    assert resp.status_code == 500
    assert "Unexpected crash" in resp.json["message"]


def test_post_message_paid_account_not_found(client, monkeypatch):
    """Paid path: account lookup returns no data → 404."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    
    class FakeChain:
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def execute(self): return SimpleNamespace(data=None) # No account
        
    monkeypatch.setattr(req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: FakeChain()))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10})
    assert resp.status_code == 404
    assert "Requester account not found" in resp.json["message"]


def test_post_message_paid_tx_no_data(client, monkeypatch):
    """Paid path: tx insert returns no data → 500."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    
    class FakeChain:
        def __init__(self): self.count = 0
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def insert(self, *a): return self
        def execute(self):
            self.count += 1
            if self.count == 1: return SimpleNamespace(data={"account_id": "acc-1"})
            return SimpleNamespace(data=[]) # tx fails
    
    chain = FakeChain()
    monkeypatch.setattr(req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10})
    assert resp.status_code == 500
    assert "Token transaction failed" in resp.json["message"]


def test_post_message_paid_msg_no_data(client, monkeypatch):
    """Paid path: message insert returns no data → 500."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    
    class FakeChain:
        def __init__(self): self.count = 0
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def insert(self, *a): return self
        def execute(self):
            self.count += 1
            if self.count == 1: return SimpleNamespace(data={"account_id": "acc-1"})
            if self.count == 2: return SimpleNamespace(data=[{"id": "tx-1"}])
            return SimpleNamespace(data=[]) # msg fails
    
    chain = FakeChain()
    monkeypatch.setattr(req_routes, "service_client", lambda: SimpleNamespace(table=lambda *a: chain))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10})
    assert resp.status_code == 500
    assert "Message creation failed" in resp.json["message"]


def test_post_message_paid_general_exception(client, monkeypatch):
    """Paid path: general exception during flow → 500."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    
    def crash_table(*a): raise Exception("Paid flow crash")
            
    monkeypatch.setattr(req_routes, "service_client", lambda: SimpleNamespace(table=crash_table))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 10})
    assert resp.status_code == 500
    assert "Paid flow crash" in resp.json["message"]
