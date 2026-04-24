"""
Input validation and basic error handling tests.
Tests that the API correctly rejects invalid input (missing fields, wrong types, etc.)
"""

import os
import uuid
import pytest
import requests

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5002")


def assert_error(res, status, error_code):
    assert res.status_code == status, (
        f"Expected {status}, got {res.status_code}. Body: {res.text}"
    )
    data = res.json()
    assert data.get("error") == error_code, (
        f"Expected error={error_code}, got {data.get('error')}. Body: {res.text}"
    )
    assert "message" in data, (
        f"Missing 'message' key in error response. Body: {res.text}"
    )


@pytest.fixture(scope="module")
def run_id():
    return uuid.uuid4().hex[:6]


@pytest.fixture(scope="module")
def user_tok(run_id):
    requests.post(
        f"{BASE_URL}/v1/auth/register",
        json={
            "name": "Val",
            "username": f"val_{run_id}",
            "email": f"val_{run_id}@example.com",
            "password": "password123",
        },
    )
    res = requests.post(
        f"{BASE_URL}/v1/auth/login",
        json={"email": f"val_{run_id}@example.com", "password": "password123"},
    )
    return res.json()["accessToken"]


class TestAuthValidation:
    def test_register_missing_fields(self):
        assert_error(
            requests.post(f"{BASE_URL}/v1/auth/register", json={}), 400, "BAD_REQUEST"
        )

    def test_login_missing_fields(self):
        assert_error(
            requests.post(f"{BASE_URL}/v1/auth/login", json={}), 400, "BAD_REQUEST"
        )

    def test_login_unknown_user(self):
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/auth/login",
                json={"email": "ghost@example.com", "password": "x"},
            ),
            401,
            "UNAUTHORIZED",
        )

    def test_logout_no_auth(self):
        assert_error(requests.post(f"{BASE_URL}/v1/auth/logout"), 401, "UNAUTHORIZED")


class TestTokenValidation:
    def test_buy_missing_fields(self, user_tok):
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/tokens/buy",
                json={"tokens": 10},
                headers={"AccessToken": user_tok},
            ),
            400,
            "BAD_REQUEST",
        )
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/tokens/buy",
                json={"cost": 5.0},
                headers={"AccessToken": user_tok},
            ),
            400,
            "BAD_REQUEST",
        )

    def test_buy_negative_tokens(self, user_tok):
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/tokens/buy",
                json={"tokens": -5, "cost": 5.0},
                headers={"AccessToken": user_tok},
            ),
            400,
            "BAD_REQUEST",
        )

    def test_redeem_missing_body(self, user_tok):
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/tokens/redeem",
                json={},
                headers={"AccessToken": user_tok},
            ),
            400,
            "BAD_REQUEST",
        )


class TestChatValidation:
    def test_create_chat_missing_fields(self, user_tok):
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/requester/chats",
                json={"tokensToSpend": 10},
                headers={"AccessToken": user_tok},
            ),
            400,
            "BAD_REQUEST",
        )

    def test_post_message_missing_field(self, user_tok):
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/requester/chats/invalid/messages",
                json={},
                headers={"AccessToken": user_tok},
            ),
            400,
            "BAD_REQUEST",
        )

    def test_review_missing_fields(self, user_tok):
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/requester/chats/invalid/review",
                json={"rating": 5},
                headers={"AccessToken": user_tok},
            ),
            400,
            "BAD_REQUEST",
        )

    def test_claim_missing_title(self, user_tok):
        assert_error(
            requests.post(
                f"{BASE_URL}/v1/responder/chats/invalid/claim",
                json={},
                headers={"AccessToken": user_tok},
            ),
            400,
            "BAD_REQUEST",
        )
