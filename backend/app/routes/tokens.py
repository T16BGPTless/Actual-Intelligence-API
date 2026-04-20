"""Token management endpoints."""

import re
import requests
import os

from datetime import datetime, UTC
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import service_client, user_client, anon_client

tokens_bp = Blueprint("tokens", __name__)


def _execute_data(query, default=None):
    """Safely read `.data` from Supabase execute responses."""
    result = query.execute()
    if result is None:
        return default
    return result.data


def _require_positive_tokens(body: dict) -> int | None:
    raw = body.get("tokens")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _account_for_user(client, user_id: str):
    res = _execute_data(
        client.table("accounts")
        .select("account_id,account_name,created_by")
        .eq("created_by", user_id)
        .order("created_at")
        .limit(1)
    )
    # Return the first dictionary if it exists, otherwise return None
    return res[0] if res else None


@tokens_bp.route("/v1/tokens", methods=["GET"])
def get_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = service_client()
    try:
        account = _account_for_user(client, str(user.id))
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))

    if not account:
        return return_error("NOT_FOUND", "User account cannot be found")

    try:
        balance_res = _execute_data(
            client.table("token_balances")
            .select("balance")
            .eq("account_id", account["account_id"])
            .limit(1)
        )
        # balance_res should be a list (0 or 1 row)
        balance = 0
        if balance_res:
            balance = int(balance_res[0]["balance"] or 0)
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))

    return (
        jsonify({"tokenBalance": balance}),
        HTTPStatus.OK,
    )


@tokens_bp.route("/v1/tokens/buy", methods=["POST"])
def buy_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    tokens = _require_positive_tokens(body)
    if tokens is None:
        return return_error("BAD_REQUEST", "Missing or invalid data: tokens required.")
    cost = body.get("cost")
    if cost is None:
        return return_error("BAD_REQUEST", "Missing or invalid data: cost required.")

    client = service_client()
    try:
        account = _account_for_user(client, str(user.id))
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))

    if not account:
        return return_error("NOT_FOUND", "User account cannot be found")

    account_id = account["account_id"]
    try:
        current = _execute_data(
            client.table("token_balances")
            .select("balance")
            .eq("account_id", account_id)
            .limit(1)
        )
        # Update parsing here
        current_balance = 0
        if current:
            current_balance = int(current[0].get("balance") or 0)
        updated_balance = current_balance + tokens

        if current:
            client.table("token_balances").update({"balance": updated_balance}).eq(
                "account_id", account_id
            ).execute()
        else:
            client.table("token_balances").insert(
                {"account_id": account_id, "balance": updated_balance}
            ).execute()

        client.table("token_transactions").insert(
            {
                "account_id": account_id,
                "txn_type": "buy",
                "amount": tokens,
                "created_by": str(user.id),
            }
        ).execute()
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))

    try:
        # Extract user's full name from session metadata, fallback to email if missing
        customer_name = "Customer"
        if hasattr(user, "user_metadata") and user.user_metadata:
            customer_name = user.user_metadata.get("name") or user.email

        today_str = datetime.now(UTC).strftime("%Y-%m-%d")

        invoice_payload = {
            "InvoiceData": {
                "supplier": {
                    "name": "Actual Intelligence",
                    "ABN": "6767676767",
                    "streetName": "UNSW, Anzac Parade",
                    "city": "Sydney",
                    "postalCode": "2000",
                    "country": "AU",
                },
                "customer": {
                    "name": customer_name,
                },
                "issueDate": today_str,
                "dueDate": today_str,
                "totalAmount": cost,
                "currency": "AUD",
                "lines": [
                    {
                        "lineId": "1",
                        "description": f"{tokens} tokens",
                        "quantity": 1,
                        "unitPrice": cost,
                        "lineTotal": cost,
                    }
                ],
                "gstPercent": 10,
            }
        }

        # Check for APIToken in incoming request headers, or default to an environment variable/placeholder
        api_token = os.environ.get("INVOICE_API_TOKEN")

        resp = requests.post(
            "https://api.gptless.au/v2/invoices/generate",
            json=invoice_payload,
            headers={"APIToken": str(api_token)},
            timeout=5,  # Prevents hanging your backend if the external API is slow
        )

        # Extract the invoice ID using regex
        invoice_ids = re.findall(r"<cbc:ID>(.+?)</cbc:ID>", resp.text)
        if invoice_ids:
            invoice_id = invoice_ids[0]

            # Send the email notification
            notify_payload = {"recipientEmail": user.email}
            requests.post(
                f"https://api.gptless.au/v2/invoices/notify/{invoice_id}",
                json=notify_payload,
                headers={"APIToken": str(api_token)},
                timeout=5,
            )
    except Exception as e:
        # We don't want to block the user receiving their tokens just because the invoice failed
        print(f"Warning: Failed to generate invoice: {str(e)}")

    return (
        jsonify(
            {
                "tokensAdded": tokens,
                "cost": cost,
                "tokenBalance": updated_balance,
            }
        ),
        HTTPStatus.OK,
    )


@tokens_bp.route("/v1/tokens/redeem", methods=["POST"])
def redeem_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    tokens = _require_positive_tokens(body)
    if tokens is None:
        return return_error("BAD_REQUEST", "Missing or invalid data: tokens required.")

    client = service_client()
    try:
        account = _account_for_user(client, str(user.id))
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))

    if not account:
        return return_error("NOT_FOUND", "User account cannot be found")

    account_id = account["account_id"]
    try:
        current = _execute_data(
            client.table("token_balances")
            .select("balance")
            .eq("account_id", account_id)
            .limit(1)
        )
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))

    # Update parsing here
    current_balance = 0
    if current:
        current_balance = int(current[0].get("balance") or 0)
    if current_balance < tokens:
        return return_error("CONFLICT", "Not enough tokens to redeem")

    updated_balance = current_balance - tokens
    try:
        client.table("token_balances").update({"balance": updated_balance}).eq(
            "account_id", account_id
        ).execute()

        client.table("token_transactions").insert(
            {
                "account_id": account_id,
                "txn_type": "redeem",
                "amount": -tokens,
                "created_by": str(user.id),
            }
        ).execute()
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))

    return (
        jsonify(
            {
                "tokensRedeemed": tokens,
                "tokenBalance": updated_balance,
            }
        ),
        HTTPStatus.OK,
    )
