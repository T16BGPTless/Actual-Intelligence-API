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


def _send_invoice(customer_name, email, tokens, cost, api_token, gst):
    """Runs the invoice generation synchronously with a 2-minute timeout."""
    try:
        today_str = datetime.now(UTC).strftime("%Y-%m-%d")

        invoice_payload = {
            "InvoiceData": {
                "supplier": {
                    "name": "Actual Intelligence",
                    "ABN": "0000000000",
                    "streetName": "UNSW, Anzac Parade",
                    "city": "Kensinton",
                    "postalCode": "2033",
                    "country": "AU",
                },
                "customer": {
                    "name": customer_name,
                },
                "issueDate": today_str,
                "dueDate": today_str,
                "totalAmount": cost * (1 + gst / 100),
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
                "gstPercent": gst,
            }
        }

        resp = requests.post(
            "https://api.gptless.au/v2/invoices/generate",
            json=invoice_payload,
            headers={"APIToken": str(api_token)},
            timeout=60,  # 2 minute wait time
        )

        # Extract the invoice ID using regex
        invoice_ids = re.findall(r"<cbc:ID>([0-9]+)</cbc:ID>", resp.text)
        if invoice_ids:
            # Guarantee invoice_id is a string
            invoice_id = str(invoice_ids[0])

            # Send the email notification
            notify_payload = {"recipientEmail": str(email)}
            requests.post(
                f"https://api.gptless.au/v2/invoices/notify/{invoice_id}",
                json=notify_payload,
                headers={"APIToken": str(api_token)},
                timeout=60,  # 2 minute wait time
            )

    except Exception as e:
        print(f"Invoice error: {str(e)}")


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

    customer_name = "Customer"
    if hasattr(user, "user_metadata") and user.user_metadata:
        customer_name = user.user_metadata.get("name") or user.email

    api_token = os.environ.get("INVOICE_API_TOKEN")

    _send_invoice(customer_name, user.email, tokens, cost, api_token, 10)

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
