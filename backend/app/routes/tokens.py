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


def _require_account_name(body: dict) -> str | None:
    account_name = body.get("accountName")
    if not isinstance(account_name, str) or not account_name.strip():
        return None
    return account_name.strip()


def _require_positive_tokens(body: dict) -> int | None:
    raw = body.get("tokens")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _developer_or_admin(access_token: str, user_id: str) -> bool:
    _ = access_token  # Auth is already validated by require_supabase_user.
    try:
        rows = _execute_data(
            service_client()
            .table("user_roles")
            .select("role")
            .eq("user_id", user_id)
            .in_("role", ["developer", "admin"])
        )
    except APIError:
        return False
    if not rows:
        return False
    return len(rows) > 0


def _account_for_name(client, account_name: str):
    return _execute_data(
        client.table("accounts")
        .select("account_id,account_name,created_by")
        .eq("account_name", account_name)
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

    body = request.get_json(silent=True) or {}
    account_name = _require_account_name(body)
    if not account_name:
        return return_error(
            "BAD_REQUEST", "Missing or invalid data: accountName is required"
        )

    client = service_client()
    try:
        account = _account_for_name(client, account_name)
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    if not account:
        return return_error("NOT_FOUND", "accountName cannot be found")
    if str(account.get("created_by")) != str(user.id):
        return return_error("FORBIDDEN")

    try:
        balance_row = _execute_data(
            client.table("token_balances")
            .select("balance")
            .eq("account_id", account["account_id"])
            .maybe_single()
        )
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    balance = int((balance_row or {}).get("balance") or 0)
    return (
        jsonify({"accountName": account["account_name"], "tokenBalance": balance}),
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
    account_name = _require_account_name(body)
    tokens = _require_positive_tokens(body)
    if not account_name or tokens is None:
        return return_error("BAD_REQUEST", "Missing or invalid data.")

    client = service_client()
    try:
        account = _account_for_name(client, account_name)
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    if not account:
        return return_error("NOT_FOUND", "accountName cannot be found")
    is_privileged = _developer_or_admin(access_token, str(user.id))
    is_owner = str(account.get("created_by")) == str(user.id)
    if not (is_privileged or is_owner):
        return return_error("FORBIDDEN")

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
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return (
        jsonify(
            {
                "accountName": account["account_name"],
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
    account_name = _require_account_name(body)
    tokens = _require_positive_tokens(body)
    if not account_name or tokens is None:
        return return_error("BAD_REQUEST", "Missing or invalid data.")

    client = service_client()
    try:
        account = _account_for_name(client, account_name)
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    if not account:
        return return_error("NOT_FOUND", "accountName cannot be found")
    is_privileged = _developer_or_admin(access_token, str(user.id))
    is_owner = str(account.get("created_by")) == str(user.id)
    if not (is_privileged or is_owner):
        return return_error("FORBIDDEN")

    account_id = account["account_id"]
    try:
        current = _execute_data(
            client.table("token_balances")
            .select("balance")
            .eq("account_id", account_id)
            .maybe_single()
        )
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    current_balance = int((current or {}).get("balance") or 0)
    if current_balance < tokens:
        return return_error("CONFLICT", "Not enough tokens to redeem")

    updated_balance = current_balance - tokens
    try:
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
                "txn_type": "redeem",
                "amount": -tokens,
                "created_by": str(user.id),
            }
        ).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return (
        jsonify(
            {
                "accountName": account["account_name"],
                "tokensRedeemed": tokens,
                "tokenBalance": updated_balance,
            }
        ),
        HTTPStatus.OK,
    )
