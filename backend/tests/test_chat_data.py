"""Unit tests for app.chat_data helpers."""

from types import SimpleNamespace

from postgrest.exceptions import APIError

from app import chat_data
from tests.conftest import QueryChain


class FakeClient:
    """Simple fake supabase client supporting table() and rpc()."""

    def __init__(self, table_data=None, rpc_data=None, rpc_error=False):
        self._table_data = table_data or {}
        self._rpc_data = rpc_data
        self._rpc_error = rpc_error

    def table(self, name):
        return QueryChain(self._table_data.get(name, []))

    def rpc(self, _name, _payload):
        if self._rpc_error:
            raise APIError({"message": "rpc failed"})
        return QueryChain(self._rpc_data)


def test_api_ts_variants():
    assert chat_data.api_ts(None) == ""
    assert chat_data.api_ts("2026-01-01T00:00:00+00:00") == "2026-01-01T00:00:00Z"
    assert chat_data.api_ts("2026-01-01T00:00:00Z") == "2026-01-01T00:00:00Z"


def test_categories_from_flask_arg_variants():
    assert chat_data.categories_from_flask_arg(None, None) is None
    assert chat_data.categories_from_flask_arg(["a,b"], None) == ["a", "b"]
    assert chat_data.categories_from_flask_arg([], "x,y") == ["x", "y"]


def test_profile_map_and_token_totals():
    client = FakeClient(
        table_data={
            "profiles": [{"user_id": "u1", "username": "u", "display_name": "U"}],
            "requests": [
                {"chat_id": "c1", "tokens_to_spend": 2},
                {"chat_id": "c1", "tokens_to_spend": 3},
            ],
        }
    )
    assert chat_data.token_totals_by_chat(client, []) == {}
    assert chat_data.profile_map(client, set()) == {}
    pmap = chat_data.profile_map(client, {"u1"})
    assert pmap["u1"]["username"] == "u"
    totals = chat_data.token_totals_by_chat(client, ["c1"])
    assert totals["c1"] == 5


def test_dict_formatters():
    chat = {
        "chat_id": "c1",
        "title": None,
        "category": None,
        "status": "open",
        "created_at": "x",
    }
    assert chat_data.chat_summary_dict(chat, 9)["chatID"] == "c1"
    msg = {
        "message_id": "m1",
        "sender_type": "requester",
        "message": "hi",
        "created_at": "x",
    }
    assert chat_data.message_dict(msg)["messageID"] == "m1"
    req = {
        "request_id": "r1",
        "request_text": "x",
        "status": "pending",
        "tokens_to_spend": 4,
        "created_at": "x",
    }
    assert chat_data.request_dict(req)["tokensSpent"] == 4


def test_build_chat_detail_and_get_chat():
    client = FakeClient(
        table_data={
            "profiles": [
                {"user_id": "u1", "username": "req", "display_name": "Req"},
                {"user_id": "u2", "username": "res", "display_name": "Res"},
            ],
            "messages": [
                {
                    "message_id": "m1",
                    "sender_type": "requester",
                    "message": "hi",
                    "created_at": "x",
                }
            ],
            "requests": [
                {
                    "request_id": "r1",
                    "request_text": "x",
                    "status": "pending",
                    "tokens_to_spend": 1,
                    "created_at": "x",
                }
            ],
            "chats": {"chat_id": "c1"},
        }
    )
    chat = {
        "chat_id": "c1",
        "requester_id": "u1",
        "responder_id": "u2",
        "title": "T",
        "category": "C",
        "status": "open",
        "created_at": "x",
    }
    detail = chat_data.build_chat_detail(client, chat)
    assert detail["requesterUsername"] == "req"
    assert detail["responderUsername"] == "res"
    assert chat_data.get_chat_or_none(client, "c1")


def test_create_chat_with_initial_request_validation_and_errors():
    client = FakeClient()
    assert chat_data.create_chat_with_initial_request(client, {"requestText": "x"}) == (
        None,
        "invalid_tokens",
    )
    assert chat_data.create_chat_with_initial_request(
        client, {"requestText": "x", "tokensToSpend": "bad"}
    ) == (
        None,
        "invalid_tokens",
    )
    assert chat_data.create_chat_with_initial_request(
        client, {"requestText": "x", "tokensToSpend": 0}
    ) == (
        None,
        "invalid_tokens",
    )
    err_client = FakeClient(rpc_error=True)
    assert chat_data.create_chat_with_initial_request(
        err_client, {"requestText": "x", "tokensToSpend": 1}
    ) == (None, "rpc_failed")


def test_create_chat_with_initial_request_payload_paths():
    bad_client = FakeClient(rpc_data={"ok": False})
    assert chat_data.create_chat_with_initial_request(
        bad_client, {"requestText": "x", "tokensToSpend": 1}
    ) == (None, "rpc_failed")
    list_client = FakeClient(rpc_data=[{"ok": True, "chat_id": "c1"}])
    payload, err = chat_data.create_chat_with_initial_request(
        list_client,
        {"requestText": "x", "tokensToSpend": 1, "title": 99, "category": 88},
    )
    assert err is None
    assert payload["chat_id"] == "c1"


def test_fulfill_request_rpc_paths():
    err_client = FakeClient(rpc_error=True)
    assert chat_data.fulfill_request_rpc(err_client, "c1", {"responseText": "ok"}) == (
        None,
        "rpc_failed",
    )

    none_client = FakeClient(rpc_data=None)
    assert chat_data.fulfill_request_rpc(none_client, "c1", {"responseText": "ok"}) == (
        None,
        "rpc_failed",
    )

    no_req_client = FakeClient(rpc_data={"ok": False, "error": "no_active_request"})
    assert chat_data.fulfill_request_rpc(
        no_req_client, "c1", {"responseText": "ok"}
    ) == (
        None,
        "no_active_request",
    )

    bad_client = FakeClient(rpc_data={"ok": False, "error": "x"})
    assert chat_data.fulfill_request_rpc(bad_client, "c1", {"responseText": "ok"}) == (
        None,
        "rpc_failed",
    )

    ok_client = FakeClient(rpc_data=[{"ok": True, "fulfillment_id": "f1"}])
    payload, err = chat_data.fulfill_request_rpc(
        ok_client, "c1", {"responseText": "ok", "attachments": "wrong-type"}
    )
    assert err is None
    assert payload["fulfillment_id"] == "f1"
