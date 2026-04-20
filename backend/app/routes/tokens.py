"""Token management endpoints."""

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import service_client, user_client

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
    return _execute_data(
        client.table("accounts")
        .select("account_id,account_name,created_by")
        .eq("created_by", user_id)
        .order("created_at")
        .limit(1)
        .maybe_single()
    )

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
        balance_row = _execute_data(
            client.table("token_balances")
            .select("balance")
            .eq("account_id", account["account_id"])
            .maybe_single()
        )
        balance = 0 if balance_row is None else int(balance_row["balance"] or 0)
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
            .maybe_single()
        )
        current_balance = int((current or {}).get("balance") or 0)
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

    return (
        jsonify(
            {
                "tokensAdded": tokens,
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
            .maybe_single()
        )
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))

    current_balance = int((current or {}).get("balance") or 0)
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
