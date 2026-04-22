"""Requester endpoints."""

from http import HTTPStatus
from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError
import datetime

from app.chat_data import (
    build_chat_detail,
    create_chat_with_initial_request,
    get_chat_or_none,
    categories_from_flask_arg,
    chat_summary_dict,
    message_dict,
)
from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import service_client, user_client

requester_bp = Blueprint("requester", __name__)


@requester_bp.route("/v1/requester/chats", methods=["POST"])
def create_chat():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    for req in ["requestText", "tokensToSpend"]:
        if req not in body:
            return return_error(
                "BAD_REQUEST", f"Missing or invalid chat data: missing field: {req}"
            )

    client = user_client(access_token)
    payload, err = create_chat_with_initial_request(client, body)
    if err == "invalid_tokens":
        return return_error("BAD_REQUEST", "Invalid tokensToSpend")
    if err:
        return return_error("INTERNAL_SERVER_ERROR", "Unable to create chat")

    chat = get_chat_or_none(client, payload["chat_id"])
    if not chat:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify(build_chat_detail(client, chat)), HTTPStatus.CREATED


@requester_bp.route("/v1/requester/chats", methods=["GET"])
def get_user_chats():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    cats = categories_from_flask_arg(
        request.args.getlist("category"), request.args.get("category")
    )
    status = request.args.get("status")

    q = client.table("chats").select("*").eq("requester_id", str(user.id))
    if cats:
        q = q.in_("category", cats)
    if status in ["open", "claimed", "closing", "closed"]:
        q = q.eq("status", status)

    try:
        data = q.order("created_at", desc=False).execute().data or []
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    results = [chat_summary_dict(client, c) for c in data]
    return jsonify(results), HTTPStatus.OK


@requester_bp.route("/v1/requester/chats/<chat_id>", methods=["GET"])
def get_chat_detail(chat_id):
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "You do not have access to this content")

    return jsonify(build_chat_detail(client, chat)), HTTPStatus.OK


@requester_bp.route("/v1/requester/chats/<chat_id>/messages", methods=["POST"])
def post_message(chat_id):
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    msg_text = body.get("message")
    if not msg_text:
        return return_error(
            "BAD_REQUEST", "Missing or invalid message data: missing field: message"
        )

    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "You do not have access to this content")
    if chat["status"] != "claimed":
        return return_error("BAD_REQUEST", "Chat is not claimed")

    tokens = body.get("tokensToSpend", 0)
    if not isinstance(tokens, int) or tokens < 0:
        return return_error(
            "BAD_REQUEST", "tokensToSpend must be a non-negative integer"
        )

    if tokens == 0:
        try:
            res = (
                client.table("messages")
                .insert(
                    {
                        "chat_id": chat_id,
                        "sender_id": str(user.id),
                        "sender_type": "requester",
                        "message": msg_text,
                        "tokens": 0,
                    }
                )
                .execute()
            )
            if not res.data:
                return return_error("INTERNAL_SERVER_ERROR", "Message insert failed")
            return jsonify(message_dict(res.data[0])), HTTPStatus.CREATED
        except Exception as e:
            return return_error("INTERNAL_SERVER_ERROR", str(e))

    try:
        s_client = service_client()
        # 1. Get account
        acc = (
            s_client.table("accounts")
            .select("account_id")
            .eq("created_by", str(user.id))
            .maybe_single()
            .execute()
        )
        if not acc.data:
            return return_error("NOT_FOUND", "Requester account not found")
        account_id = acc.data["account_id"]

        # 2. Check and Update balance
        bal_res = (
            s_client.table("token_balances")
            .select("balance")
            .eq("account_id", account_id)
            .maybe_single()
            .execute()
        )
        if not bal_res.data or bal_res.data["balance"] < tokens:
            return return_error("BAD_REQUEST", "invalid_tokens")

        s_client.table("token_balances").update(
            {"balance": bal_res.data["balance"] - tokens}
        ).eq("account_id", account_id).execute()

        # 3. Log transaction
        s_client.table("token_transactions").insert(
            {
                "account_id": account_id,
                "txn_type": "spend",
                "amount": -tokens,
                "chat_id": chat_id,
                "created_by": str(user.id),
            }
        ).execute()

        # 4. Log message
        res_msg = (
            s_client.table("messages")
            .insert(
                {
                    "chat_id": chat_id,
                    "sender_id": str(user.id),
                    "sender_type": "requester",
                    "message": msg_text,
                    "tokens": tokens,
                }
            )
            .execute()
        )
        if not res_msg.data:
            return return_error("INTERNAL_SERVER_ERROR", "Message creation failed")

        # 5. Update chat tokens_spent
        current_spent = chat.get("tokens_spent") or 0
        s_client.table("chats").update({"tokens_spent": current_spent + tokens}).eq(
            "chat_id", chat_id
        ).execute()

        return jsonify(message_dict(res_msg.data[0])), HTTPStatus.CREATED

    except APIError as e:
        msg = getattr(e, "message", "") or ""
        if "invalid_tokens" in msg.lower() or "insufficient" in msg.lower():
            return return_error("BAD_REQUEST", "invalid_tokens")
        return return_error("INTERNAL_SERVER_ERROR", str(e))
    except Exception as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))


@requester_bp.route("/v1/requester/chats/<chat_id>/review", methods=["POST"])
def review_chat(chat_id):
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    rating = body.get("rating")
    resolved = body.get("resolved")

    if rating is None or resolved is None:
        return return_error("BAD_REQUEST", "Missing rating or resolved")

    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return return_error("BAD_REQUEST", "Rating must be an integer between 1 and 5")

    if not isinstance(resolved, bool):
        return return_error("BAD_REQUEST", "Resolved must be a boolean")

    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "You do not have access to this content")
    if chat["status"] != "closing":
        return return_error("BAD_REQUEST", "Chat is not in closing state")

    try:
        s_client = service_client()
        # 1. Payout to responder if applicable
        if chat.get("responder_id") and chat.get("tokens_spent", 0) > 0:
            tokens = chat["tokens_spent"]
            # Get responder account
            res_acc = (
                s_client.table("accounts")
                .select("account_id")
                .eq("created_by", str(chat["responder_id"]))
                .maybe_single()
                .execute()
            )
            if res_acc.data:
                account_id = res_acc.data["account_id"]
                # Log transaction
                s_client.table("token_transactions").insert(
                    {
                        "account_id": account_id,
                        "txn_type": "adjustment",
                        "amount": tokens,
                        "chat_id": chat_id,
                        "created_by": str(user.id),
                    }
                ).execute()
                # Update balance
                bal_res = (
                    s_client.table("token_balances")
                    .select("balance")
                    .eq("account_id", account_id)
                    .maybe_single()
                    .execute()
                )
                current_bal = bal_res.data["balance"] if bal_res.data else 0
                s_client.table("token_balances").update(
                    {"balance": current_bal + tokens}
                ).eq("account_id", account_id).execute()

        # 2. Update chat with review info and set status to closed
        res = (
            s_client.table("chats")
            .update(
                {
                    "rating": rating,
                    "resolved": resolved,
                    "status": "closed",
                    "closed_at": datetime.datetime.now(
                        datetime.timezone.utc
                    ).isoformat(),
                }
            )
            .eq("chat_id", chat_id)
            .execute()
        )

        if not res.data:
            return return_error("INTERNAL_SERVER_ERROR")

        return jsonify(build_chat_detail(client, res.data[0])), HTTPStatus.OK
    except Exception as e:
        return return_error("INTERNAL_SERVER_ERROR", str(e))
