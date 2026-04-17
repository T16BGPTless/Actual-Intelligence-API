"""Unit tests for requester routes."""

from http import HTTPStatus
from types import SimpleNamespace
from app.routes import requester as req_routes
from app.routes.helpers import return_error
from postgrest.exceptions import APIError

def _patch_auth(monkeypatch):
    monkeypatch.setattr(req_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(req_routes, "require_supabase_user", lambda t: (SimpleNamespace(id="user-1"), None))
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace())
    
    class FakeServiceTable:
        def select(self, *a): return self
        def eq(self, *a): return self
        def maybe_single(self): return self
        def in_(self, *a): return self
        def execute(self): return SimpleNamespace(data={"account_id": "acc-1", "balance": 1000})
        def update(self, *a): return self
        def insert(self, *a): return self
    monkeypatch.setattr(req_routes, "service_client", lambda *a: SimpleNamespace(table=lambda *a: FakeServiceTable()))
        

def test_create_chat_missing_fields(client, monkeypatch):
    _patch_auth(monkeypatch)
    resp = client.post("/v1/requester/chats", json={"requestText": "Test"})
    assert resp.status_code == 400
    assert resp.json["error"] == "BAD_REQUEST"

def test_create_chat_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "create_chat_with_initial_request", lambda *a: ({"chat_id": "test-id"}, None))
    
    # 500 error if get_chat_or_none fails
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post("/v1/requester/chats", json={"requestText": "test", "tokensToSpend": 5})
    assert resp.status_code == 500
    
    # success branch
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"chat_id": "test-id", "status": "open"})
    monkeypatch.setattr(req_routes, "build_chat_detail", lambda *a: {"chatID": "test-id", "status": "open"})
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
        def __init__(self):
            self.update_calls = []
        def update(self, *a):
            self.update_calls.append(a)
            return self
        def eq(self, *a): return self
        def insert(self, *a): return self
        def execute(self):
            return SimpleNamespace(data=[{
                "sender_type": "requester",
                "message": "hello",
                "tokens": 1,
                "created_at": "2026-04-16T12:00:00+00:00"
            }])
    fake_table = FakeTable()
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: fake_table))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "hello", "tokensToSpend": 1})
    assert resp.status_code == 201
    assert fake_table.update_calls, "Expected token-spend path to trigger an update call"

def test_review_chat_success(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "closing"})
    class FakeTable:
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): pass
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTable()))
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5, "resolved": True})
    assert resp.status_code == 200

def test_auth_failures(client, monkeypatch):
    monkeypatch.setattr(req_routes, "require_access_token", lambda: (None, return_error("UNAUTHORIZED")))
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 401
    
    monkeypatch.setattr(req_routes, "require_access_token", lambda: ("tok", None))
    monkeypatch.setattr(req_routes, "require_supabase_user", lambda t: (None, return_error("UNAUTHORIZED")))
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 401

def test_api_error_handling(client, monkeypatch):
    _patch_auth(monkeypatch)
    class FakeErrorQ:
        def select(self, *a): return self
        def eq(self, *a): return self
        def in_(self, *a): return self
        def order(self, *a, **k): return self
        def execute(self): raise APIError({"message": "db error"})
        
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeErrorQ()))
    resp = client.get("/v1/requester/chats")
    assert resp.status_code == 500

def test_get_chat_detail_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.get("/v1/requester/chats/1")
    assert resp.status_code == 404
    
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1"})
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
    
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "other"})
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "x"})
    assert resp.status_code == 403
    
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "closed"})
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "x"})
    assert resp.status_code == 400
    
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    # Test invalid tokens types
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "x", "tokensToSpend": "5"})
    assert resp.status_code == 400
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "x", "tokensToSpend": -2})
    assert resp.status_code == 400
    
    class FakeTableErr:
        def insert(self, *a): return self
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): raise APIError({"message": "db error"})
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTableErr()))
    resp = client.post("/v1/requester/chats/1/messages", json={"message": "M", "tokensToSpend": 10})
    assert resp.status_code == 500

def test_review_chat_errors(client, monkeypatch):
    _patch_auth(monkeypatch)
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: None)
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5, "resolved": True})
    assert resp.status_code == 404
    
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "other"})
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5, "resolved": True})
    assert resp.status_code == 403
    
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "claimed"})
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5, "resolved": True})
    assert resp.status_code == 400
    
    resp = client.post("/v1/requester/chats/1/review", json={})
    assert resp.status_code == 400
    
    resp = client.post("/v1/requester/chats/1/review", json={"resolved": True})
    assert resp.status_code == 400
    
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5})
    assert resp.status_code == 400
    
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 6, "resolved": True})
    assert resp.status_code == 400
    
    resp = client.post("/v1/requester/chats/1/review", json={"rating": "5", "resolved": True})
    assert resp.status_code == 400
    
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5, "resolved": "yes"})
    assert resp.status_code == 400
    
    monkeypatch.setattr(req_routes, "get_chat_or_none", lambda *a: {"requester_id": "user-1", "status": "closing"})
    class FakeTableErr:
        def update(self, *a): return self
        def eq(self, *a): return self
        def execute(self): raise APIError({"message": "db"})
    monkeypatch.setattr(req_routes, "user_client", lambda *a: SimpleNamespace(table=lambda *a: FakeTableErr()))
    resp = client.post("/v1/requester/chats/1/review", json={"rating": 5, "resolved": True})
    assert resp.status_code == 500

