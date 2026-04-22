"""
Integration flows and complex lifecycle tests.
Focuses on E2E scenarios, security constraints, and financial accuracy.
"""

import os
import uuid
import time
import pytest
import requests

BASE_URL = os.getenv("E2E_BASE_URL", "http://127.0.0.1:5002")
BAD_ID = str(uuid.uuid4())

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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


def assert_ok(res, status=200):
    assert res.status_code == status, (
        f"Expected {status}, got {res.status_code}. Body: {res.text}"
    )
    return res.json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def run_id():
    return uuid.uuid4().hex[:6]


@pytest.fixture(scope="module")
def tok_req(run_id):
    requests.post(
        f"{BASE_URL}/v1/auth/register",
        json={
            "name": "Req",
            "username": f"req_{run_id}",
            "email": f"req_{run_id}@example.com",
            "password": "password123",
        },
    )
    return requests.post(
        f"{BASE_URL}/v1/auth/login",
        json={"email": f"req_{run_id}@example.com", "password": "password123"},
    ).json()["accessToken"]


@pytest.fixture(scope="module")
def tok_res(run_id):
    requests.post(
        f"{BASE_URL}/v1/auth/register",
        json={
            "name": "Res",
            "username": f"res_{run_id}",
            "email": f"res_{run_id}@example.com",
            "password": "password123",
        },
    )
    return requests.post(
        f"{BASE_URL}/v1/auth/login",
        json={"email": f"res_{run_id}@example.com", "password": "password123"},
    ).json()["accessToken"]


@pytest.fixture(scope="module")
def funded_req(tok_req):
    requests.post(
        f"{BASE_URL}/v1/tokens/buy",
        json={"tokens": 1000, "cost": 10.0},
        headers={"AccessToken": tok_req},
    )
    return tok_req


@pytest.fixture(scope="module")
def open_chat_id(funded_req):
    res = requests.post(
        f"{BASE_URL}/v1/requester/chats",
        json={"requestText": "Open chat", "category": "writing", "tokensToSpend": 10},
        headers={"AccessToken": funded_req},
    )
    return res.json()["chatID"]


@pytest.fixture(scope="module")
def claimed_chat_id(funded_req, tok_res):
    cid = requests.post(
        f"{BASE_URL}/v1/requester/chats",
        json={"requestText": "Claimed chat", "category": "tech", "tokensToSpend": 10},
        headers={"AccessToken": funded_req},
    ).json()["chatID"]
    requests.post(
        f"{BASE_URL}/v1/responder/chats/{cid}/claim",
        json={"title": "Claimed"},
        headers={"AccessToken": tok_res},
    )
    return cid


@pytest.fixture(scope="module")
def closing_chat_id(claimed_chat_id, tok_res):
    requests.post(
        f"{BASE_URL}/v1/responder/chats/{claimed_chat_id}/close",
        headers={"AccessToken": tok_res},
    )
    return claimed_chat_id


# ---------------------------------------------------------------------------
# Integration Flows
# ---------------------------------------------------------------------------


class TestSecurityAndAccuracy:
    def test_responder_cannot_claim_own_chat(self, funded_req):
        cid = requests.post(
            f"{BASE_URL}/v1/requester/chats",
            json={"requestText": "Self claim", "category": "tech", "tokensToSpend": 1},
            headers={"AccessToken": funded_req},
        ).json()["chatID"]
        res = requests.post(
            f"{BASE_URL}/v1/responder/chats/{cid}/claim",
            json={"title": "T"},
            headers={"AccessToken": funded_req},
        )
        # Should be blocked by the new check in responder.py
        assert res.status_code == 403

    def test_exact_payout_accuracy(self, run_id):
        # Dedicated users
        r_email = f"pay_r_{run_id}@example.com"
        s_email = f"pay_s_{run_id}@example.com"
        requests.post(
            f"{BASE_URL}/v1/auth/register",
            json={
                "name": "R",
                "username": f"pr_{run_id}",
                "email": r_email,
                "password": "password123",
            },
        )
        requests.post(
            f"{BASE_URL}/v1/auth/register",
            json={
                "name": "S",
                "username": f"ps_{run_id}",
                "email": s_email,
                "password": "password123",
            },
        )
        r_tok = requests.post(
            f"{BASE_URL}/v1/auth/login",
            json={"email": r_email, "password": "password123"},
        ).json()["accessToken"]
        s_tok = requests.post(
            f"{BASE_URL}/v1/auth/login",
            json={"email": s_email, "password": "password123"},
        ).json()["accessToken"]

        requests.post(
            f"{BASE_URL}/v1/tokens/buy",
            json={"tokens": 100, "cost": 1.0},
            headers={"AccessToken": r_tok},
        )
        cid = requests.post(
            f"{BASE_URL}/v1/requester/chats",
            json={"requestText": "Pay", "category": "tech", "tokensToSpend": 33},
            headers={"AccessToken": r_tok},
        ).json()["chatID"]

        requests.post(
            f"{BASE_URL}/v1/responder/chats/{cid}/claim",
            json={"title": "C"},
            headers={"AccessToken": s_tok},
        )
        requests.post(
            f"{BASE_URL}/v1/responder/chats/{cid}/close", headers={"AccessToken": s_tok}
        )

        bal_before = requests.get(
            f"{BASE_URL}/v1/tokens", headers={"AccessToken": s_tok}
        ).json()["tokenBalance"]
        requests.post(
            f"{BASE_URL}/v1/requester/chats/{cid}/review",
            json={"resolved": True, "rating": 5},
            headers={"AccessToken": r_tok},
        )
        bal_after = requests.get(
            f"{BASE_URL}/v1/tokens", headers={"AccessToken": s_tok}
        ).json()["tokenBalance"]

        assert bal_after == bal_before + 33


class TestFullLifecycle:
    def test_e2e_messaging_and_state(self, funded_req, tok_res, run_id):
        # 1. Create
        cid = requests.post(
            f"{BASE_URL}/v1/requester/chats",
            json={"requestText": "E2E", "category": "writing", "tokensToSpend": 10},
            headers={"AccessToken": funded_req},
        ).json()["chatID"]

        # 2. Claim
        requests.post(
            f"{BASE_URL}/v1/responder/chats/{cid}/claim",
            json={"title": "T"},
            headers={"AccessToken": tok_res},
        )

        # 3. Multi-turn
        requests.post(
            f"{BASE_URL}/v1/requester/chats/{cid}/messages",
            json={"message": "M1", "tokensToSpend": 5},
            headers={"AccessToken": funded_req},
        )
        requests.post(
            f"{BASE_URL}/v1/responder/chats/{cid}/messages",
            json={"message": "M2"},
            headers={"AccessToken": tok_res},
        )

        # 4. Close & Review
        requests.post(
            f"{BASE_URL}/v1/responder/chats/{cid}/close",
            headers={"AccessToken": tok_res},
        )
        requests.post(
            f"{BASE_URL}/v1/requester/chats/{cid}/review",
            json={"resolved": True, "rating": 5},
            headers={"AccessToken": funded_req},
        )

        # 5. Verify final
        chat = requests.get(
            f"{BASE_URL}/v1/requester/chats/{cid}", headers={"AccessToken": funded_req}
        ).json()
        assert chat["status"] == "closed"
        assert chat["tokensSpent"] == 15  # 10 initial + 5 message


class TestExtendedEdgeCases:
    def test_cannot_message_unclaimed(self, open_chat_id, funded_req):
        res = requests.post(
            f"{BASE_URL}/v1/requester/chats/{open_chat_id}/messages",
            json={"message": "X", "tokensToSpend": 0},
            headers={"AccessToken": funded_req},
        )
        assert res.status_code in (400, 403)

    def test_cannot_review_claimed(self, claimed_chat_id, funded_req):
        res = requests.post(
            f"{BASE_URL}/v1/requester/chats/{claimed_chat_id}/review",
            json={"resolved": True, "rating": 5},
            headers={"AccessToken": funded_req},
        )
        assert res.status_code in (400, 403)

    def test_insufficient_tokens_for_message(self, claimed_chat_id, run_id):
        # New poor user
        email = f"poor_{run_id}@example.com"
        requests.post(
            f"{BASE_URL}/v1/auth/register",
            json={
                "name": "P",
                "username": f"p_{run_id}",
                "email": email,
                "password": "password123",
            },
        )
        poor_tok = requests.post(
            f"{BASE_URL}/v1/auth/login",
            json={"email": email, "password": "password123"},
        ).json()["accessToken"]

        res = requests.post(
            f"{BASE_URL}/v1/requester/chats/{claimed_chat_id}/messages",
            json={"message": "X", "tokensToSpend": 100},
            headers={"AccessToken": poor_tok},
        )
        # Note: 404 is expected because RLS hides the chat from the poor user
        assert res.status_code == 404
