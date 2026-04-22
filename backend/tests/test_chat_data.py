"""Unit tests for chat data access."""

from app.chat_data import (
    api_ts,
    categories_from_flask_arg,
    profile_map,
    chat_summary_dict,
    message_dict,
    get_chat_or_none,
    create_chat_with_initial_request,
    build_chat_detail,
)
from types import SimpleNamespace


def test_api_ts():
    assert api_ts(None) == ""
    assert api_ts("2026-04-01T00:00:00+00:00") == "2026-04-01T00:00:00Z"
    assert api_ts("raw string") == "raw string"


def test_categories_from_flask_arg():
    assert categories_from_flask_arg(None, None) == None
    assert categories_from_flask_arg(["cat1"], "cat2") == ["cat1"]
    assert categories_from_flask_arg(["cat1, cat2"], None) == ["cat1", "cat2"]
    assert categories_from_flask_arg(None, "cat1, cat2") == ["cat1", "cat2"]


def test_chat_summary_dict():
    chat = {"chat_id": "123", "status": "open"}
    res = chat_summary_dict(None, chat)
    assert res["chatID"] == "123"
    assert res["status"] == "open"
    assert res["tokens"] == 0


def test_message_dict():
    msg = {"sender_type": "requester", "message": "hi"}
    res = message_dict(msg)
    assert res["senderType"] == "requester"
    assert res["message"] == "hi"
    assert res["tokens"] == 0


def test_get_chat_or_none(monkeypatch):
    class FakeQ:
        def select(self, *a):
            return self

        def eq(self, *a):
            return self

        def maybe_single(self):
            return self

        def execute(self):
            return SimpleNamespace(data={"chat_id": "123"})

    class FakeClient:
        def table(self, t):
            return FakeQ()

    assert get_chat_or_none(FakeClient(), "123")["chat_id"] == "123"


def test_create_chat_with_initial_request_invalid_tokens():
    res, err = create_chat_with_initial_request(None, {"tokensToSpend": -1})
    assert err == "invalid_tokens"
    res, err = create_chat_with_initial_request(None, {"tokensToSpend": "abc"})
    assert err == "invalid_tokens"


def test_create_chat_with_initial_request_success():
    class FakeRes:
        data = [{"ok": True, "chat_id": "123"}]

    class FakeUpd:
        def eq(self, *a):
            return self

        def execute(self):
            return self

    class FakeClient:
        def rpc(self, *a, **k):
            return self

        def execute(self):
            return FakeRes()

        def table(self, t):
            return self

        def update(self, d):
            return FakeUpd()

from postgrest.exceptions import APIError


def _make_fake_client(profile_rows=None, message_rows=None, chat_data=None):
    """Build a minimal fake supabase client for chat_data functions."""

    class FakeQ:
        def __init__(self, data):
            self._data = data

        def select(self, *a):
            return self

        def in_(self, *a):
            return self

        def eq(self, *a):
            return self

        def maybe_single(self):
            return self

        def order(self, *a, **k):
            return self

        def execute(self):
            return SimpleNamespace(data=self._data)

    class FakeClient:
        def table(self, name):
            if name == "profiles":
                return FakeQ(profile_rows or [])
            if name == "messages":
                return FakeQ(message_rows or [])
            if name == "chats":
                return FakeQ(chat_data)
            return FakeQ(None)

    return FakeClient()


# ---------------------------------------------------------------------------
# profile_map
# ---------------------------------------------------------------------------

def test_profile_map_empty_ids_returns_empty():
    from app.chat_data import profile_map
    assert profile_map(None, set()) == {}
    assert profile_map(None, {""}) == {}


def test_profile_map_returns_keyed_by_user_id():
    from app.chat_data import profile_map
    client = _make_fake_client(
        profile_rows=[
            {"user_id": "u1", "username": "alice", "display_name": "Alice"},
            {"user_id": "u2", "username": "bob", "display_name": "Bob"},
        ]
    )
    result = profile_map(client, {"u1", "u2"})
    assert result["u1"]["username"] == "alice"
    assert result["u2"]["username"] == "bob"


# ---------------------------------------------------------------------------
# build_chat_detail
# ---------------------------------------------------------------------------

def test_build_chat_detail_with_messages():
    from app.chat_data import build_chat_detail
    client = _make_fake_client(
        profile_rows=[
            {"user_id": "u1", "username": "alice", "display_name": "Alice"},
        ],
        message_rows=[
            {
                "message_id": "m1",
                "sender_type": "requester",
                "message": "hello",
                "tokens": 2,
                "created_at": "2026-04-01T10:00:00+00:00",
            }
        ],
    )
    chat = {
        "chat_id": "c1",
        "requester_id": "u1",
        "responder_id": None,
        "status": "open",
        "title": "My Chat",
        "original_request": "some request",
        "category": "tech",
        "tokens_spent": 5,
        "created_at": "2026-04-01T09:00:00+00:00",
    }
    result = build_chat_detail(client, chat)
    assert result["chatID"] == "c1"
    assert result["requesterUsername"] == "alice"
    assert result["responderUsername"] is None
    assert len(result["messages"]) == 1
    assert result["messages"][0]["senderType"] == "requester"
    assert result["tokensSpent"] == 5


def test_build_chat_detail_with_responder():
    from app.chat_data import build_chat_detail
    client = _make_fake_client(
        profile_rows=[
            {"user_id": "u1", "username": "alice", "display_name": "Alice"},
            {"user_id": "u2", "username": "bob", "display_name": "Bob"},
        ],
        message_rows=[],
    )
    chat = {
        "chat_id": "c2",
        "requester_id": "u1",
        "responder_id": "u2",
        "status": "claimed",
        "title": None,
        "original_request": None,
        "category": None,
        "tokens_spent": None,
        "created_at": None,
    }
    result = build_chat_detail(client, chat)
    assert result["responderUsername"] == "bob"
    assert result["tokensSpent"] == 0
    assert result["originalRequest"] == ""


# ---------------------------------------------------------------------------
# get_chat_or_none branches
# ---------------------------------------------------------------------------

def test_get_chat_or_none_returns_none_when_execute_returns_falsy():
    from app.chat_data import get_chat_or_none

    class FakeQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def execute(self): return None

    class FakeClient:
        def table(self, *a): return FakeQ()

    assert get_chat_or_none(FakeClient(), "x") is None


def test_get_chat_or_none_returns_dict_directly():
    from app.chat_data import get_chat_or_none

    class FakeQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def execute(self): return {"chat_id": "c1"}

    class FakeClient:
        def table(self, *a): return FakeQ()

    result = get_chat_or_none(FakeClient(), "c1")
    assert result["chat_id"] == "c1"


def test_get_chat_or_none_returns_data_from_namespace():
    from app.chat_data import get_chat_or_none

    class FakeQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def execute(self): return SimpleNamespace(data={"chat_id": "c2"})

    class FakeClient:
        def table(self, *a): return FakeQ()

    result = get_chat_or_none(FakeClient(), "c2")
    assert result["chat_id"] == "c2"


# ---------------------------------------------------------------------------
# create_chat_with_initial_request branches
# ---------------------------------------------------------------------------

def test_create_chat_missing_tokens_to_spend():
    from app.chat_data import create_chat_with_initial_request
    res, err = create_chat_with_initial_request(None, {"requestText": "hi"})
    assert err == "invalid_tokens"
    assert res is None


def test_create_chat_rpc_api_error_returns_rpc_failed():
    from app.chat_data import create_chat_with_initial_request

    class FakeClient:
        def rpc(self, *a, **k): return self
        def execute(self):
            raise APIError({"message": "rpc error"})

    res, err = create_chat_with_initial_request(
        FakeClient(), {"tokensToSpend": 5, "requestText": "hi"}
    )
    assert err == "rpc_failed"
    assert res is None


def test_create_chat_rpc_returns_empty_list():
    from app.chat_data import create_chat_with_initial_request

    class FakeClient:
        def rpc(self, *a, **k): return self
        def execute(self): return SimpleNamespace(data=[])

    res, err = create_chat_with_initial_request(
        FakeClient(), {"tokensToSpend": 5, "requestText": "hi"}
    )
    assert err == "rpc_failed"


def test_create_chat_rpc_returns_not_ok():
    from app.chat_data import create_chat_with_initial_request

    class FakeClient:
        def rpc(self, *a, **k): return self
        def execute(self): return SimpleNamespace(data=[{"ok": False}])

    res, err = create_chat_with_initial_request(
        FakeClient(), {"tokensToSpend": 5, "requestText": "hi"}
    )
    assert err == "rpc_failed"


def test_create_chat_title_update_api_error_returns_payload_with_warning():
    from app.chat_data import create_chat_with_initial_request

    class FakeUpd:
        def eq(self, *a): return self
        def execute(self):
            raise APIError({"message": "update failed"})

    class FakeClient:
        def rpc(self, *a, **k): return self
        def execute(self): return SimpleNamespace(data=[{"ok": True, "chat_id": "c1"}])
        def table(self, *a): return self
        def update(self, *a): return FakeUpd()

    res, err = create_chat_with_initial_request(
        FakeClient(), {"tokensToSpend": 5, "requestText": "hi", "title": "My Title"}
    )
    assert err == "title_update_failed"
    assert res["chat_id"] == "c1"
