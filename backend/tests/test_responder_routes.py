"""Unit tests for responder routes."""

from http import HTTPStatus
from types import SimpleNamespace
from app.routes import responder as res_routes
from app.routes.helpers import return_error
from postgrest.exceptions import APIError

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
        def is_(self, *a): return self
        def execute(self): return SimpleNamespace(data=[{"chat_id": "1"}])
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTable()))
    resp = client.post("/v1/responder/chats/1/claim", json={"title": "A Title"})
    assert resp.status_code == 200

def test_post_message_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"responder_id": "user-1", "status": "claimed"})
    class FakeTable:
        def insert(self, *a): return self
        def execute(self): 
            return SimpleNamespace(data=[{
                "sender_type": "responder",
                "message": "hello",
                "tokens": 0,
                "created_at": "2026-04-16T12:00:00+00:00"
            }])
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTable()))
    resp = client.post("/v1/responder/chats/1/messages", json={"message": "hello"})
    assert resp.status_code == 201

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

def test_auth_failures(client, monkeypatch):
    monkeypatch.setattr(res_routes, "require_access_token", lambda: (None, return_error("UNAUTHORIZED")))
    resp = client.get("/v1/responder/chats/unclaimed")
    assert resp.status_code == 401
    
    monkeypatch.setattr(res_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(res_routes, "require_supabase_user", lambda t: (None, return_error("UNAUTHORIZED")))
    resp = client.get("/v1/responder/chats/unclaimed")
    assert resp.status_code == 401

def test_api_error_handling(client, monkeypatch):
    _patch_auth(monkeypatch)
    def raise_api_error(*a, **k):
        raise APIError({"message": "db error"})
        
    class FakeErrorQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def neq(self, *a): return self
        def order(self, *a, **k): return self
        def execute(self): raise_api_error()
        
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeErrorQ()))
    resp = client.get("/v1/responder/chats/unclaimed")
    assert resp.status_code == 500
    
    resp2 = client.get("/v1/responder/chats")
    assert resp2.status_code == 500

def test_claim_chat_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
    resp = client.post("/v1/responder/chats/1/claim", json={})
    assert resp.status_code == 400
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post("/v1/responder/chats/1/claim", json={"title": "T"})
    assert resp.status_code == 404
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"status": "claimed", "claim_state": "claimed"})
    resp = client.post("/v1/responder/chats/1/claim", json={"title": "T"})
    assert resp.status_code == 409
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"status": "open", "claim_state": "unclaimed"})
    class FakeTableErr:
        def __init__(self, c="db", code=""):
            self.msg = c
            self.code = code
        def update(self, *a): return self
        def eq(self, *a): return self
        def is_(self, *a): return self
        def execute(self): raise APIError({"message": self.msg, "code": self.code})
        
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTableErr()))
    resp = client.post("/v1/responder/chats/1/claim", json={"title": "T"})
    assert resp.status_code == 500
    
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTableErr(c="new row violates row-level security policy", code="42501")))
    resp = client.post("/v1/responder/chats/1/claim", json={"title": "T"})
    assert resp.status_code == 403
    
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTableErr(code="23505")))
    resp = client.post("/v1/responder/chats/1/claim", json={"title": "T"})
    assert resp.status_code == 409

def test_get_chat_detail_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: None)
    resp = client.get("/v1/responder/chats/1")
    assert resp.status_code == 404
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"status": "claimed", "responder_id": "other"})
    resp = client.get("/v1/responder/chats/1")
    assert resp.status_code == 403

def test_post_message_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
    resp = client.post("/v1/responder/chats/1/messages", json={})
    assert resp.status_code == 400
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post("/v1/responder/chats/1/messages", json={"message": "M"})
    assert resp.status_code == 404
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"responder_id": "user-1", "status": "closing"})
    resp = client.post("/v1/responder/chats/1/messages", json={"message": "M"})
    assert resp.status_code == 400
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"responder_id": "user-1", "status": "claimed"})
    class FakeTableErr:
        def insert(self, *a): return self
        def execute(self): raise APIError({"message": "db"})
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTableErr()))
    resp = client.post("/v1/responder/chats/1/messages", json={"message": "M"})
    assert resp.status_code == 500

def test_close_chat_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post("/v1/responder/chats/1/close", json={"responseText": "Hello!"})
    assert resp.status_code == 404
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"responder_id": "other"})
    resp = client.post("/v1/responder/chats/1/close", json={"responseText": "Hello!"})
    assert resp.status_code == 403
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"responder_id": "user-1", "status": "closing"})
    resp = client.post("/v1/responder/chats/1/close", json={"responseText": "Hello!"})
    assert resp.status_code == 409
    
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"responder_id": "user-1", "status": "claimed"})
    class FakeTableErr:
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): raise APIError({"message": "db"})
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTableErr()))
    resp = client.post("/v1/responder/chats/1/close", json={"responseText": "Hello!"})
    assert resp.status_code == 500

def test_close_chat_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(res_routes, "get_chat_or_none", lambda *a: {"responder_id": "user-1", "status": "claimed"})
    class FakeTable:
        def update(self, *a): return self
        def eq(self, *a): return self
        def is_(self, *a): return self
        def execute(self): return SimpleNamespace(data=[{"chat_id": "1"}])
    monkeypatch.setattr(res_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTable()))
    resp = client.post("/v1/responder/chats/1/close", json={"responseText": "Hello!"})
    assert resp.status_code == 200
