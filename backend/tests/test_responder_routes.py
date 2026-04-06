"""Unit tests for responder routes."""

from types import SimpleNamespace

from postgrest.exceptions import APIError

from app.routes import responder as responder_routes
from tests.conftest import QueryChain


def _ok_auth(monkeypatch, user_id="res-1"):
    monkeypatch.setattr(responder_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        responder_routes,
        "require_supabase_user",
        lambda _t: (SimpleNamespace(id=user_id), None),
    )


def test_list_chats_success(client, monkeypatch):
    _ok_auth(monkeypatch)
    fake = QueryChain([{"chat_id": "c1", "status": "open"}])
    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: fake),
    )
    monkeypatch.setattr(responder_routes, "categories_from_flask_arg", lambda *_a: None)
    monkeypatch.setattr(
        responder_routes, "token_totals_by_chat", lambda _c, _ids: {"c1": 9}
    )
    monkeypatch.setattr(
        responder_routes,
        "chat_summary_dict",
        lambda chat, tokens: {"chatID": chat["chat_id"], "tokens": tokens},
    )
    resp = client.get("/v1/responder/chats")
    assert resp.status_code == 200
    assert resp.json[0]["chatID"] == "c1"


def test_list_chats_with_category_filter_branch(client, monkeypatch):
    _ok_auth(monkeypatch)
    fake = QueryChain([{"chat_id": "c1", "status": "open"}])
    monkeypatch.setattr(
        responder_routes, "user_client", lambda _t: SimpleNamespace(table=lambda _n: fake)
    )
    monkeypatch.setattr(responder_routes, "categories_from_flask_arg", lambda *_a: ["dev"])
    monkeypatch.setattr(responder_routes, "token_totals_by_chat", lambda *_a: {"c1": 1})
    monkeypatch.setattr(
        responder_routes, "chat_summary_dict", lambda chat, _tokens: {"chatID": chat["chat_id"]}
    )
    resp = client.get("/v1/responder/chats")
    assert resp.status_code == 200


def test_list_unclaimed_success(client, monkeypatch):
    _ok_auth(monkeypatch)
    fake = QueryChain([{"chat_id": "u1", "status": "open"}])
    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: fake),
    )
    monkeypatch.setattr(responder_routes, "categories_from_flask_arg", lambda *_a: None)
    monkeypatch.setattr(
        responder_routes, "token_totals_by_chat", lambda _c, _ids: {"u1": 2}
    )
    monkeypatch.setattr(
        responder_routes,
        "chat_summary_dict",
        lambda chat, tokens: {"chatID": chat["chat_id"], "tokens": tokens},
    )
    resp = client.get("/v1/responder/chats/unclaimed")
    assert resp.status_code == 200
    assert resp.json[0]["chatID"] == "u1"


def test_list_unclaimed_with_category_filter_branch(client, monkeypatch):
    _ok_auth(monkeypatch)
    fake = QueryChain([{"chat_id": "u1", "status": "open"}])
    monkeypatch.setattr(
        responder_routes, "user_client", lambda _t: SimpleNamespace(table=lambda _n: fake)
    )
    monkeypatch.setattr(responder_routes, "categories_from_flask_arg", lambda *_a: ["dev"])
    monkeypatch.setattr(responder_routes, "token_totals_by_chat", lambda *_a: {"u1": 1})
    monkeypatch.setattr(
        responder_routes, "chat_summary_dict", lambda chat, _tokens: {"chatID": chat["chat_id"]}
    )
    resp = client.get("/v1/responder/chats/unclaimed")
    assert resp.status_code == 200


def test_list_unclaimed_user_error(client, monkeypatch):
    monkeypatch.setattr(responder_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        responder_routes, "require_supabase_user", lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert client.get("/v1/responder/chats/unclaimed").status_code == 401


def test_get_chat_not_found(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(responder_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(responder_routes, "get_chat_or_none", lambda _c, _id: None)
    resp = client.get("/v1/responder/chats/missing")
    assert resp.status_code == 404


def test_get_chat_success_and_user_error(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(responder_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(responder_routes, "get_chat_or_none", lambda *_a: {"chat_id": "c1"})
    monkeypatch.setattr(responder_routes, "build_chat_detail", lambda *_a: {"chatID": "c1"})
    assert client.get("/v1/responder/chats/c1").status_code == 200

    monkeypatch.setattr(responder_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        responder_routes, "require_supabase_user", lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert client.get("/v1/responder/chats/c1").status_code == 401


def test_claim_chat_conflict_if_already_claimed(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(responder_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(
        responder_routes,
        "get_chat_or_none",
        lambda _c, _id: {"responder_id": "x", "status": "open"},
    )
    resp = client.post("/v1/responder/chats/c1/claim")
    assert resp.status_code == 409


def test_claim_chat_success(client, monkeypatch):
    _ok_auth(monkeypatch, user_id="res-1")
    chain = QueryChain([{"chat_id": "c1", "status": "open"}])
    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: chain),
    )
    monkeypatch.setattr(
        responder_routes,
        "get_chat_or_none",
        lambda _c, _id: {
            "responder_id": None,
            "claim_state": "unclaimed",
            "status": "open",
        },
    )
    monkeypatch.setattr(
        responder_routes,
        "build_chat_detail",
        lambda _c, chat: {"chatID": chat["chat_id"]},
    )
    resp = client.post("/v1/responder/chats/c1/claim")
    assert resp.status_code == 200
    assert resp.json["chatID"] == "c1"


def test_claim_chat_forbidden_on_permission_error(client, monkeypatch):
    _ok_auth(monkeypatch)

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "permission denied", "code": "42501"})

    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: BadChain()),
    )
    monkeypatch.setattr(
        responder_routes,
        "get_chat_or_none",
        lambda _c, _id: {
            "responder_id": None,
            "claim_state": "unclaimed",
            "status": "open",
        },
    )
    resp = client.post("/v1/responder/chats/c1/claim")
    assert resp.status_code == 403


def test_send_message_success(client, monkeypatch):
    _ok_auth(monkeypatch)
    fake = QueryChain({"message_id": "m2", "sender_type": "responder", "message": "ok"})
    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: fake),
    )
    monkeypatch.setattr(
        responder_routes, "get_chat_or_none", lambda _c, _id: {"chat_id": _id}
    )
    monkeypatch.setattr(
        responder_routes, "message_dict", lambda row: {"messageID": row["message_id"]}
    )
    resp = client.post("/v1/responder/chats/c1/messages", json={"message": "ok"})
    assert resp.status_code == 201
    assert resp.json["messageID"] == "m2"


def test_fulfill_request_missing_field(client, monkeypatch):
    _ok_auth(monkeypatch)
    resp = client.post("/v1/responder/chats/c1/fulfill-request", json={})
    assert resp.status_code == 400


def test_fulfill_request_no_active_request_conflict(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(responder_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(
        responder_routes, "get_chat_or_none", lambda _c, _id: {"chat_id": _id}
    )
    monkeypatch.setattr(
        responder_routes,
        "fulfill_request_rpc",
        lambda _c, _id, _b: (None, "no_active_request"),
    )
    resp = client.post(
        "/v1/responder/chats/c1/fulfill-request",
        json={"responseText": "done"},
    )
    assert resp.status_code == 409


def test_fulfill_request_success(client, monkeypatch):
    _ok_auth(monkeypatch)
    fake = QueryChain(
        {
            "fulfillment_id": "f1",
            "request_id": "r1",
            "response_text": "done",
            "created_at": "2026-04-01T00:00:00+00:00",
        }
    )
    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: fake),
    )
    monkeypatch.setattr(
        responder_routes, "get_chat_or_none", lambda _c, _id: {"chat_id": _id}
    )
    monkeypatch.setattr(
        responder_routes,
        "fulfill_request_rpc",
        lambda _c, _id, _b: ({"fulfillment_id": "f1", "request_id": "r1"}, None),
    )
    monkeypatch.setattr(responder_routes, "api_ts", lambda _v: "2026-04-01T00:00:00Z")
    resp = client.post(
        "/v1/responder/chats/c1/fulfill-request",
        json={"responseText": "done"},
    )
    assert resp.status_code == 201
    assert resp.json["fulfillmentID"] == "f1"


def test_responder_routes_unauthorized_paths(client, monkeypatch):
    monkeypatch.setattr(
        responder_routes,
        "require_access_token",
        lambda: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    assert client.get("/v1/responder/chats").status_code == 401
    assert client.get("/v1/responder/chats/unclaimed").status_code == 401
    assert client.get("/v1/responder/chats/c1").status_code == 401


def test_responder_routes_user_check_error(client, monkeypatch):
    monkeypatch.setattr(responder_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        responder_routes,
        "require_supabase_user",
        lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401)),
    )
    assert client.get("/v1/responder/chats").status_code == 401
    assert client.post("/v1/responder/chats/c1/claim").status_code == 401


def test_claim_chat_bad_request_and_internal_error(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(responder_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(
        responder_routes,
        "get_chat_or_none",
        lambda *_a: {"responder_id": None, "claim_state": "claimed", "status": "open"},
    )
    assert client.post("/v1/responder/chats/c1/claim").status_code == 400

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "boom", "code": "XX000"})

    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: BadChain()),
    )
    monkeypatch.setattr(
        responder_routes,
        "get_chat_or_none",
        lambda *_a: {
            "responder_id": None,
            "claim_state": "unclaimed",
            "status": "open",
        },
    )
    assert client.post("/v1/responder/chats/c1/claim").status_code == 500


def test_claim_chat_conflict_when_update_returns_empty(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: QueryChain([])),
    )
    monkeypatch.setattr(
        responder_routes,
        "get_chat_or_none",
        lambda *_a: {
            "responder_id": None,
            "claim_state": "unclaimed",
            "status": "open",
        },
    )
    assert client.post("/v1/responder/chats/c1/claim").status_code == 409


def test_send_message_missing_or_not_found(client, monkeypatch):
    _ok_auth(monkeypatch)
    assert client.post("/v1/responder/chats/c1/messages", json={}).status_code == 400
    monkeypatch.setattr(responder_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(responder_routes, "get_chat_or_none", lambda *_a: None)
    assert (
        client.post(
            "/v1/responder/chats/c1/messages", json={"message": "x"}
        ).status_code
        == 404
    )

    monkeypatch.setattr(
        responder_routes, "require_access_token", lambda: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert client.post("/v1/responder/chats/c1/messages", json={"message": "x"}).status_code == 401
    monkeypatch.setattr(responder_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        responder_routes, "require_supabase_user", lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert client.post("/v1/responder/chats/c1/messages", json={"message": "x"}).status_code == 401


def test_fulfill_request_not_found_and_internal(client, monkeypatch):
    _ok_auth(monkeypatch)
    monkeypatch.setattr(responder_routes, "user_client", lambda _t: object())
    monkeypatch.setattr(responder_routes, "get_chat_or_none", lambda *_a: None)
    assert (
        client.post(
            "/v1/responder/chats/c1/fulfill-request", json={"responseText": "x"}
        ).status_code
        == 404
    )

    monkeypatch.setattr(
        responder_routes, "get_chat_or_none", lambda *_a: {"chat_id": "c1"}
    )
    monkeypatch.setattr(
        responder_routes, "fulfill_request_rpc", lambda *_a: (None, "rpc_failed")
    )
    assert (
        client.post(
            "/v1/responder/chats/c1/fulfill-request", json={"responseText": "x"}
        ).status_code
        == 500
    )

    fake = QueryChain(None)
    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: fake),
    )
    monkeypatch.setattr(
        responder_routes,
        "fulfill_request_rpc",
        lambda *_a: ({"fulfillment_id": "f1", "request_id": "r1"}, None),
    )
    assert (
        client.post(
            "/v1/responder/chats/c1/fulfill-request", json={"responseText": "x"}
        ).status_code
        == 500
    )


def test_fulfill_request_auth_user_and_select_error_paths(client, monkeypatch):
    monkeypatch.setattr(
        responder_routes, "require_access_token", lambda: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert (
        client.post("/v1/responder/chats/c1/fulfill-request", json={"responseText": "x"}).status_code
        == 401
    )

    monkeypatch.setattr(responder_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(
        responder_routes, "require_supabase_user", lambda _t: (None, ({"error": "UNAUTHORIZED"}, 401))
    )
    assert (
        client.post("/v1/responder/chats/c1/fulfill-request", json={"responseText": "x"}).status_code
        == 401
    )

    _ok_auth(monkeypatch)
    monkeypatch.setattr(responder_routes, "get_chat_or_none", lambda *_a: {"chat_id": "c1"})
    monkeypatch.setattr(
        responder_routes,
        "fulfill_request_rpc",
        lambda *_a: ({"fulfillment_id": "f1", "request_id": "r1"}, None),
    )

    class BadChain(QueryChain):
        def execute(self):
            raise APIError({"message": "x"})

    monkeypatch.setattr(
        responder_routes,
        "user_client",
        lambda _t: SimpleNamespace(table=lambda _n: BadChain()),
    )
    assert (
        client.post("/v1/responder/chats/c1/fulfill-request", json={"responseText": "x"}).status_code
        == 500
    )
