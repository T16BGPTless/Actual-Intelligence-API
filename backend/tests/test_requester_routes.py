"""Unit tests for requester routes."""

from types import SimpleNamespace

from postgrest.exceptions import APIError

from app.routes import requester as requester_routes
from tests.conftest import QueryChain


def _ok_auth(monkeypatch, user_id="user-1"):
    monkeypatch.setattr(requester_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        requester_routes,
        "require_supabase_user",
        lambda _t: (SimpleNamespace(id=user_id), None),
    )


def test_create_chat_requires_request_text(client, monkeypatch):
    _ok_auth(monkeypatch)
    resp = client.post("/v1/requester/chats", json={})
    assert resp.status_code == 400


def test_create_chat_success(client, monkeypatch):
    _ok_auth(monkeypatch)
    fake_client = object()
    monkeypatch.setattr(requester_routes, "user_client", lambda _t: fake_client)
    monkeypatch.setattr(
        requester_routes,
        "create_chat_with_initial_request",
        lambda _c, _b: ({"chat_id": "chat_1"}, None),
    )
    monkeypatch.setattr(
        requester_routes,
        "get_chat_or_none",
        lambda _c, _id: {"chat_id": "chat_1"},
    )
    monkeypatch.setattr(
        requester_routes,
        "build_chat_detail",
        lambda _c, _chat: {"chatID": "chat_1"},
    )
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "hello", "tokensToSpend": 1}
    )
    assert resp.status_code == 201
    assert resp.json["chatID"] == "chat_1"


def test_list_chats_success(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    fake = QueryChain([{"chat_id": "c1", "status": "open", "created_at": "x"}])
    monkeypatch.setattr(
        requester_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: fake),
    )
    monkeypatch.setattr(
        requester_routes, "token_totals_by_chat", lambda _c, _ids: {"c1": 5}
    )
    monkeypatch.setattr(
        requester_routes,
        "chat_summary_dict",
        lambda chat, tokens: {"chatID": chat["chat_id"], "tokens": tokens},
    )
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 200
    assert resp.json[0]["chatID"] == "c1"


def test_get_chat_not_found(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(requester_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(requester_routes, "get_chat_or_none", lambda _c, _id: None)
    resp = client.get("/v1/requester/chats/missing")
    assert resp.status_code == 404


def test_get_chat_success_and_user_error(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(requester_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(requester_routes, "get_chat_or_none", lambda _c, _id: {"chat_id": "c1"})
    monkeypatch.setattr(
        requester_routes, "build_chat_detail", lambda _c, _chat: {"chatID": "c1"}
    )
    assert client.get("/v1/requester/chats/c1").status_code == 200

    monkeypatch.setattr(requester_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        requester_routes,
        "require_supabase_user",
        lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    assert client.get("/v1/requester/chats/c1").status_code == 401


def test_send_message_success(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    fake = QueryChain({"message_id": "m1", "sender_type": "requester", "message": "hi"})
    monkeypatch.setattr(
        requester_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: fake),
    )
    monkeypatch.setattr(
        requester_routes, "get_chat_or_none", lambda _c, _id: {"chat_id": _id}
    )
    monkeypatch.setattr(
        requester_routes,
        "message_dict",
        lambda row: {"messageID": row["message_id"]},
    )
    resp = client.post("/v1/requester/chats/c1/messages", json={"message": "hi"})
    assert resp.status_code == 201
    assert resp.json["messageID"] == "m1"


def test_send_message_forbidden_on_api_error(client, monkeypatch):
    _ok_auth(monkeypatch)

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "denied", "code": "42501"})

    monkeypatch.setattr(
        requester_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: BadChain()),
    )
    monkeypatch.setattr(
        requester_routes, "get_chat_or_none", lambda _c, _id: {"chat_id": _id}
    )
    resp = client.post("/v1/requester/chats/c1/messages", json={"message": "hi"})
    assert resp.status_code == 403


def test_add_request_validates_tokens(client, monkeypatch):
    _ok_auth(monkeypatch)
    resp = client.post("/v1/requester/chats/c1/requests", json={"requestText": "x"})
    assert resp.status_code == 400


def test_add_request_success(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")
    fake = QueryChain(
        {
            "request_id": "r1",
            "request_text": "x",
            "status": "pending",
            "tokens_to_spend": 3,
        }
    )
    monkeypatch.setattr(
        requester_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: fake),
    )
    monkeypatch.setattr(
        requester_routes, "get_chat_or_none", lambda _c, _id: {"chat_id": _id}
    )
    monkeypatch.setattr(
        requester_routes, "request_dict", lambda row: {"requestID": row["request_id"]}
    )
    resp = client.post(
        "/v1/requester/chats/c1/requests",
        json={"requestText": "x", "tokensToSpend": 3},
    )
    assert resp.status_code == 201
    assert resp.json["requestID"] == "r1"


def test_add_request_not_found_branch(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(requester_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(requester_routes, "get_chat_or_none", lambda *_a: None)
    resp = client.post(
        "/v1/requester/chats/c1/requests",
        json={"requestText": "x", "tokensToSpend": 1},
    )
    assert resp.status_code == 404


def test_close_chat_success(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(
        requester_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: QueryChain()),
    )
    monkeypatch.setattr(
        requester_routes, "get_chat_or_none", lambda _c, _id: {"chat_id": _id}
    )
    resp = client.post("/v1/requester/chats/c1/close")
    assert resp.status_code == 200


def test_requester_routes_unauthorized_paths(client, monkeypatch):
    monkeypatch.setattr(
        requester_routes,
        "require_access_token",
        lambda: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    assert client.get("/v1/requester/chats").status_code == 401
    assert (
        client.post("/v1/requester/chats", json={"requestText": "x"}).status_code == 401
    )
    assert client.get("/v1/requester/chats/c1").status_code == 401


def test_requester_routes_user_check_error(client, monkeypatch):
    monkeypatch.setattr(requester_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        requester_routes,
        "require_supabase_user",
        lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    assert client.get("/v1/requester/chats").status_code == 401
    assert (
        client.post("/v1/requester/chats", json={"requestText": "x"}).status_code == 401
    )


def test_create_chat_internal_failures(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(requester_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(
        requester_routes,
        "create_chat_with_initial_request",
        lambda *_a: (None, "rpc_failed"),
    )
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "x", "tokensToSpend": 1}
    )
    assert resp.status_code == 500

    monkeypatch.setattr(
        requester_routes,
        "create_chat_with_initial_request",
        lambda *_a: ({"chat_id": "c1"}, None),
    )
    monkeypatch.setattr(requester_routes, "get_chat_or_none", lambda *_a: None)
    resp = client.post(
        "/v1/requester/chats", json={"requestText": "x", "tokensToSpend": 1}
    )
    assert resp.status_code == 500


def test_create_chat_invalid_tokens_branch(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(requester_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(
        requester_routes, "create_chat_with_initial_request", lambda *_a: (None, "invalid_tokens")
    )
    resp = client.post("/v1/requester/chats", json={"requestText": "x", "tokensToSpend": 0})
    assert resp.status_code == 400


def test_send_message_missing_body_field(client, monkeypatch):
    _ok_auth(monkeypatch)
    resp = client.post("/v1/requester/chats/c1/messages", json={})
    assert resp.status_code == 400


def test_send_message_auth_and_user_errors(client, monkeypatch):
    monkeypatch.setattr(
        requester_routes, "require_access_token", lambda: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert client.post("/v1/requester/chats/c1/messages", json={"message": "x"}).status_code == 401
    monkeypatch.setattr(requester_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        requester_routes, "require_supabase_user", lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert client.post("/v1/requester/chats/c1/messages", json={"message": "x"}).status_code == 401


def test_send_message_not_found(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(requester_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(requester_routes, "get_chat_or_none", lambda *_a: None)
    resp = client.post("/v1/requester/chats/c1/messages", json={"message": "x"})
    assert resp.status_code == 404


def test_add_request_conflict_on_api_error(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="u1")

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "x"})

    monkeypatch.setattr(
        requester_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: BadChain()),
    )
    monkeypatch.setattr(
        requester_routes, "get_chat_or_none", lambda *_a: {"chat_id": "c1"}
    )
    resp = client.post(
        "/v1/requester/chats/c1/requests",
        json={"requestText": "x", "tokensToSpend": 3},
    )
    assert resp.status_code == 409


def test_add_request_validation_branches(client, monkeypatch):
    _ok_auth(monkeypatch)
    assert client.post("/v1/requester/chats/c1/requests", json={}).status_code == 400
    assert (
        client.post(
            "/v1/requester/chats/c1/requests",
            json={"requestText": "x", "tokensToSpend": "bad"},
        ).status_code
        == 400
    )
    assert (
        client.post(
            "/v1/requester/chats/c1/requests",
            json={"requestText": "x", "tokensToSpend": 0},
        ).status_code
        == 400
    )


def test_add_request_auth_and_user_errors(client, monkeypatch):
    monkeypatch.setattr(
        requester_routes, "require_access_token", lambda: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert (
        client.post(
            "/v1/requester/chats/c1/requests",
            json={"requestText": "x", "tokensToSpend": 1},
        ).status_code
        == 401
    )
    monkeypatch.setattr(requester_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        requester_routes, "require_supabase_user", lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert (
        client.post(
            "/v1/requester/chats/c1/requests",
            json={"requestText": "x", "tokensToSpend": 1},
        ).status_code
        == 401
    )


def test_close_chat_not_found_and_forbidden(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(requester_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(requester_routes, "get_chat_or_none", lambda *_a: None)
    assert client.post("/v1/requester/chats/c1/close").status_code == 404

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "x"})

    monkeypatch.setattr(
        requester_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: BadChain()),
    )
    monkeypatch.setattr(
        requester_routes, "get_chat_or_none", lambda *_a: {"chat_id": "c1"}
    )
    assert client.post("/v1/requester/chats/c1/close").status_code == 403


def test_close_chat_auth_and_user_errors(client, monkeypatch):
    monkeypatch.setattr(
        requester_routes, "require_access_token", lambda: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert client.post("/v1/requester/chats/c1/close").status_code == 401
    monkeypatch.setattr(requester_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        requester_routes, "require_supabase_user", lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert client.post("/v1/requester/chats/c1/close").status_code == 401
