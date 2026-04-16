"""Unit tests for requester routes."""

from http import HTTPStatus
from types import SimpleNamespace
from app.routes import requester as req_routes

def _patch_auth(monkeypatch):
    monkeypatch.setattr(req_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(req_routes, "require_supabase_user", lambda t: (SimpleNamespace(id="user-1"), None))
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace())

def test_create_chat_missing_fields(client, monkeypatch):
    _patch_auth(monkeypatch)
    resp = client.post("/v1/requester/chats", json={"requestText": "Test"})
    assert resp.status_code == 400
    assert resp.json["error"] == "BAD_REQUEST"

def test_create_chat_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "create_chat_with_initial_request", lambda *a: ({"chat_id": "test-id"}, None))
    resp = client.post("/v1/requester/chats", json={"requestText": "test", "tokensToSpend": 5})
    assert resp.status_code == 201
    assert resp.json["chatID"] == "test-id"

def test_get_user_chats(client, monkeypatch):
    _patch_auth(monkeypatch)
    class FakeQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def in_(self, *a): return self
        def order(self, *a, **k): return self
        def execute(self): return SimpleNamespace(data=[{"chat_id": "1", "status": "open"}])
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeQ()))
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 200
    assert len(resp.json) == 1

def test_get_chat_detail_forbidden(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "other-user"})
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 403

def test_post_message_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    class FakeTable:
        def update(self, *a): return self
        def eq(self, *a): return self
        def insert(self, *a): return self
        def execute(self): pass
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTable()))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hello", "tokens": 1})
    assert resp.status_code == 201

def test_review_chat_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "closing"})
    class FakeTable:
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): pass
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTable()))
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5})
    assert resp.status_code == 200
