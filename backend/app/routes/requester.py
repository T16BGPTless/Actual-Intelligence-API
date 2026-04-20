"""Requester endpoints."""

from http import HTTPStatus
from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

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

    try:
        res = client.rpc(
            "post_requester_message",
            {"p_chat_id": chat_id, "p_message": msg_text, "p_tokens": tokens},
        ).execute()

        payload = res.data
        if not payload:
            return return_error("INTERNAL_SERVER_ERROR", "Message insert failed")

        msg_row = payload
    except APIError as e:
        import json

        if str(getattr(e, "code", "")) == "200" or str(getattr(e, "code", "")) == "201":
            try:
                raw_bytes_str = getattr(e, "details", "")
                if isinstance(raw_bytes_str, bytes):
                    raw_bytes_str = raw_bytes_str.decode("utf-8")
                elif (
                    isinstance(raw_bytes_str, str)
                    and raw_bytes_str.startswith("b'")
                    and raw_bytes_str.endswith("'")
                ):
                    raw_bytes_str = raw_bytes_str[2:-1].replace("'", "'")
                msg_row = json.loads(raw_bytes_str)
                return jsonify(msg_row), 201
            except Exception:
                pass

        msg = getattr(e, "message", "") or ""
        if "invalid_tokens" in msg:
            return return_error("BAD_REQUEST", "invalid_tokens")
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify(message_dict(msg_row)), HTTPStatus.CREATED


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
    sclient = service_client()
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "You do not have access to this content")
    if chat["status"] != "closing":
        return return_error("BAD_REQUEST", "Chat is not closing")

    upd = {"status": "closed", "resolved": resolved, "rating": rating}

    try:
        # Payout tokens to responder
        responder_id = chat.get("responder_id")
        tokens_spent = int(chat.get("tokens_spent") or 0)

        if responder_id and tokens_spent > 0:
            res_account = (
                sclient.table("accounts")
                .select("account_id")
                .eq("created_by", responder_id)
                .maybe_single()
                .execute()
                .data
            )
            if res_account:
                acc_id = res_account["account_id"]
                # get current balance
                cur = (
                    sclient.table("token_balances")
                    .select("balance")
                    .eq("account_id", acc_id)
                    .maybe_single()
                    .execute()
                    .data
                )
                cur_bal = int((cur or {}).get("balance") or 0)

                sclient.table("token_balances").update(
                    {"balance": cur_bal + tokens_spent}
                ).eq("account_id", acc_id).execute()
                sclient.table("token_transactions").insert(
                    {
                        "account_id": acc_id,
                        "txn_type": "adjustment",
                        "amount": tokens_spent,
                        "chat_id": chat_id,
                        "created_by": str(user.id),
                    }
                ).execute()

        client.table("chats").update(upd).eq("chat_id", chat_id).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify({"message": "Chat successfully closed."}), HTTPStatus.OK
