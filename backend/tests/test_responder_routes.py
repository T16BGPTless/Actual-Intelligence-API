"""Unit tests for responder routes."""

from http import HTTPStatus
from types import SimpleNamespace
from app.routes import responder as res_routes

def _patch_auth(monkeypatch):
    monkeypatch.setattr(res_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(res_routes, "require_supabase_user", lambda t: (SimpleNamespace(id="user-1"), None))
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace())

def test_browse_chats(client, monkeypatch):
    _patch_auth(monkeypatch)
    class FakeQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def neq(self, *a): return self
        def order(self, *a, **k): return self
        def execute(self): return SimpleNamespace(data=[{"chat_id": "2", "status": "open"}])
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeQ()))
    resp = client.get("/v1/responder/chats/unclaimed")
    assert resp.status_code == 200

def test_claimed_chats(client, monkeypatch):
    _patch_auth(monkeypatch)
    class FakeQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def neq(self, *a): return self
        def order(self, *a, **k): return self
        def execute(self): return SimpleNamespace(data=[{"chat_id": "2", "status": "open"}])
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeQ()))
    resp = client.get("/v1/responder/chats")
    assert resp.status_code == 200

def test_claim_chat_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"status": "open", "claim_state": "unclaimed"})
    class FakeTable:
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): pass
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTable()))
    resp = client.post("/v1/responder/chats/1/claim", json={"title": "A Title"})
    assert resp.status_code == 200

def test_post_message_forbidden(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"responder_id": "other-user"})
    resp = client.post("/v1/responder/chats/1/messages", json={"message": "hi"})
    assert resp.status_code == 403

def test_get_chat_detail_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"status": "open", "responder_id": "user-1"})
    monkeypatch.setattr(res_routes, "build_chat_detail", lambda *a: {"chatID": "123"})
    resp = client.get("/v1/responder/chats/1")
    assert resp.status_code == 200
