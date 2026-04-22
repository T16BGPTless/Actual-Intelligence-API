"""
Smoke tests for all endpoints defined in swagger.yaml.
Ensures every endpoint exists and returns a non-500 response for valid-ish data.
"""

import os
import uuid
import pytest
import requests

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5002")

@pytest.fixture(scope="module")
def run_id():
    return uuid.uuid4().hex[:6]

@pytest.fixture(scope="module")
def user(run_id):
    # Register & Login to get a token
    email = f"swagger_{run_id}@example.com"
    passw = "password123"
    res_reg = requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "Swagger User", "username": f"swagger_{run_id}",
        "email": email, "password": passw
    })
    import time
    time.sleep(0.5) # Allow DB commit
    res = requests.post(f"{BASE_URL}/v1/auth/login", json={"email": email, "password": passw})
    token = res.json()["accessToken"]
    # Fund user for create_chat tests
    requests.post(f"{BASE_URL}/v1/tokens/buy", json={"tokens": 1000, "cost": 10.0}, headers={"AccessToken": token})
    return token

@pytest.fixture(scope="module")
def chat_id(user):
    # Fund user
    requests.post(f"{BASE_URL}/v1/tokens/buy", json={"tokens": 100, "cost": 10.0}, headers={"AccessToken": user})
    # Create chat
    res = requests.post(f"{BASE_URL}/v1/requester/chats", 
                        json={"requestText": "Swagger test chat", "category": "writing", "tokensToSpend": 10},
                        headers={"AccessToken": user})
    return res.json()["chatID"]

# --- Auth ---
def test_swagger_auth_register(run_id):
    res = requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "New", "username": f"new_{run_id}", "email": f"new_{run_id}@example.com", "password": "password123"
    })
    assert res.status_code in (201, 409)

def test_swagger_auth_login(run_id):
    # Independent register + login
    email = f"login_test_{run_id}@example.com"
    requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "Login Test", "username": f"login_test_{run_id}",
        "email": email, "password": "password123"
    })
    res = requests.post(f"{BASE_URL}/v1/auth/login", json={"email": email, "password": "password123"})
    assert res.status_code == 200

def test_swagger_auth_me(user):
    res = requests.get(f"{BASE_URL}/v1/auth/me", headers={"AccessToken": user})
    assert res.status_code == 200

def test_swagger_auth_logout(run_id):
    # Use a fresh user for logout test to avoid invalidating the module-scoped 'user' token
    email = f"logout_{run_id}@example.com"
    requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "Logout User", "username": f"logout_{run_id}",
        "email": email, "password": "password123"
    })
    tok = requests.post(f"{BASE_URL}/v1/auth/login", json={"email": email, "password": "password123"}).json()["accessToken"]
    res = requests.post(f"{BASE_URL}/v1/auth/logout", headers={"AccessToken": tok})
    assert res.status_code == 200

# --- Tokens ---
def test_swagger_tokens_get(user):
    res = requests.get(f"{BASE_URL}/v1/tokens", headers={"AccessToken": user})
    assert res.status_code == 200

def test_swagger_tokens_buy(user):
    res = requests.post(f"{BASE_URL}/v1/tokens/buy", json={"tokens": 1, "cost": 0.1}, headers={"AccessToken": user})
    assert res.status_code == 200

def test_swagger_tokens_redeem(user):
    res = requests.post(f"{BASE_URL}/v1/tokens/redeem", json={"tokens": 1}, headers={"AccessToken": user})
    assert res.status_code in (200, 409)

# --- Requester ---
def test_swagger_requester_chats_list(user):
    res = requests.get(f"{BASE_URL}/v1/requester/chats", headers={"AccessToken": user})
    assert res.status_code == 200

def test_swagger_requester_chats_create(user):
    res = requests.post(f"{BASE_URL}/v1/requester/chats", 
                        json={"requestText": "hit", "category": "tech", "tokensToSpend": 1},
                        headers={"AccessToken": user})
    assert res.status_code == 201

def test_swagger_requester_chats_detail(user, chat_id):
    res = requests.get(f"{BASE_URL}/v1/requester/chats/{chat_id}", headers={"AccessToken": user})
    assert res.status_code == 200

def test_swagger_requester_chats_messages(user, chat_id, run_id):
    # To message as requester, chat MUST be claimed.
    # We use a second user to claim it.
    res_claim = requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "Claimer", "username": f"claimer_{run_id}",
        "email": f"claimer_{run_id}@example.com", "password": "password123"
    })
    claimer_tok = requests.post(f"{BASE_URL}/v1/auth/login", json={
        "email": f"claimer_{run_id}@example.com", "password": "password123"
    }).json()["accessToken"]
    
    requests.post(f"{BASE_URL}/v1/responder/chats/{chat_id}/claim",
                  json={"title": "I claim you"}, headers={"AccessToken": claimer_tok})
    
    res = requests.post(f"{BASE_URL}/v1/requester/chats/{chat_id}/messages",
                        json={"message": "ping", "tokensToSpend": 1}, headers={"AccessToken": user})
    assert res.status_code == 201

def test_swagger_requester_chats_review(user, chat_id):
    # Need chat to be in 'closing' state for 200
    # But as a smoke test, 400 is also acceptable as long as it's not 500/404
    res = requests.post(f"{BASE_URL}/v1/requester/chats/{chat_id}/review",
                        json={"resolved": True, "rating": 5}, headers={"AccessToken": user})
    assert res.status_code in (200, 400)

# --- Responder ---
def test_swagger_responder_chats_list(user):
    res = requests.get(f"{BASE_URL}/v1/responder/chats", headers={"AccessToken": user})
    assert res.status_code == 200

def test_swagger_responder_chats_unclaimed(user):
    res = requests.get(f"{BASE_URL}/v1/responder/chats/unclaimed", headers={"AccessToken": user})
    assert res.status_code == 200

def test_swagger_responder_chats_detail(user, chat_id):
    res = requests.get(f"{BASE_URL}/v1/responder/chats/{chat_id}", headers={"AccessToken": user})
    assert res.status_code in (200, 403, 404)

def test_swagger_responder_chats_claim(user, chat_id):
    res = requests.post(f"{BASE_URL}/v1/responder/chats/{chat_id}/claim",
                        json={"title": "claim"}, headers={"AccessToken": user})
    assert res.status_code in (200, 409, 403)

def test_swagger_responder_chats_messages(user, chat_id):
    res = requests.post(f"{BASE_URL}/v1/responder/chats/{chat_id}/messages",
                        json={"message": "pong"}, headers={"AccessToken": user})
    assert res.status_code in (201, 403)

def test_swagger_responder_chats_close(user, chat_id):
    res = requests.post(f"{BASE_URL}/v1/responder/chats/{chat_id}/close",
                        json={}, headers={"AccessToken": user})
    assert res.status_code in (200, 403, 409)
