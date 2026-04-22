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

    class FakeRpc:
        def __init__(self):
            self.rpc_calls = []

        def execute(self):
            return SimpleNamespace(
                data={
                    "sender_type": "requester",
                    "message": "hello",
                    "tokens": 1,
                    "created_at": "2026-04-16T12:00:00+00:00",
                }
            )

    class FakeClient:
        def __init__(self):
            self.fake_rpc = FakeRpc()

        def rpc(self, *a, **k):
            self.fake_rpc.rpc_calls.append((a, k))
            return self.fake_rpc

    fake_client = FakeClient()
    monkeypatch.setattr(req_routes, "user_client", lambda *a: fake_client)
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hello", "tokensToSpend": 1}
    )
    assert resp.status_code == 201
    assert fake_client.fake_rpc.rpc_calls, (
        "Expected token-spend path to trigger an RPC call"
    )


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

    class FakeRpcErr:
        def execute(self):
            raise APIError({"message": "db error"})

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(rpc=lambda *a, **k: FakeRpcErr()),
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "M", "tokensToSpend": 10}
    )
    assert resp.status_code == 500

    class FakeRpcErrTokens:
        def execute(self):
            raise APIError({"message": "invalid_tokens"})

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(rpc=lambda *a, **k: FakeRpcErrTokens()),
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
# post_message APIError with code 200/201 (lines 146-159)
# ---------------------------------------------------------------------------

def test_post_message_api_error_code_200_with_valid_json_details(client, monkeypatch):
    """APIError with code '200' and valid JSON bytes in details → 201."""
    import json
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )

    msg_payload = {"sender_type": "requester", "message": "hi", "tokens": 0, "created_at": "2026-04-01"}

    class FakeRpcOK:
        def execute(self):
            err = APIError({"message": "ok"})
            err.code = "200"
            err.details = json.dumps(msg_payload).encode("utf-8")
            raise err

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(rpc=lambda *a, **k: FakeRpcOK()),
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0}
    )
    assert resp.status_code == 201


def test_post_message_api_error_code_200_with_bad_details_falls_through(client, monkeypatch):
    """APIError with code '200' but unparseable details → falls through to 500."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )

    class FakeRpcBad:
        def execute(self):
            err = APIError({"message": "ok"})
            err.code = "200"
            err.details = "not json at all!"
            raise err

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(rpc=lambda *a, **k: FakeRpcBad()),
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0}
    )
    assert resp.status_code == 500


def test_post_message_api_error_code_201_bytes_string_format(client, monkeypatch):
    """APIError code 201 with b'...' string in details is parsed and returns 201."""
    import json
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )

    msg_payload = {"sender_type": "requester", "message": "hi", "tokens": 0, "created_at": "now"}
    raw = json.dumps(msg_payload)
    bytes_str = "b'" + raw + "'"

    class FakeRpc201:
        def execute(self):
            err = APIError({"message": "ok"})
            err.code = "201"
            err.details = bytes_str
            raise err

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(rpc=lambda *a, **k: FakeRpc201()),
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0}
    )
    assert resp.status_code == 201


def test_post_message_rpc_returns_none_data(client, monkeypatch):
    """rpc returns no data → 500."""
    _patch_auth(monkeypatch)
    monkeypatch.setattr(
        req_routes,
        "get_chat_or_none",
        lambda *a: {"requester_id": "user-1", "status": "claimed"},
    )

    class FakeRpcNone:
        def execute(self): return SimpleNamespace(data=None)

    monkeypatch.setattr(
        req_routes,
        "user_client",
        lambda *a: SimpleNamespace(rpc=lambda *a, **k: FakeRpcNone()),
    )
    resp = client.post(
        "/v1/requester/chats/1/messages", json={"message": "hi", "tokensToSpend": 0}
    )
    assert resp.status_code == 500

