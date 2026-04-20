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

    res, err = create_chat_with_initial_request(
        FakeClient(), {"tokensToSpend": 5, "requestText": "Test"}
    )
    assert not err
    assert res["chat_id"] == "123"
