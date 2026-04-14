"""Requester side endpoints."""

from datetime import UTC, datetime
from http import HTTPStatus

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from app.chat_data import (
    build_chat_detail,
    chat_summary_dict,
    create_chat_with_initial_request,
    get_chat_or_none,
    message_dict,
    request_dict,
    token_totals_by_chat,
)
from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import user_client

requester_bp = Blueprint("requester", __name__)


@requester_bp.route("/v1/requester/chats", methods=["POST"])
def create_chat():
    access_token, error = require_access_token()
    if error:
        return error
    _, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    if "requestText" not in body:
        return return_error(
            "BAD_REQUEST", "Missing or invalid chat data: missing field: requestText"
        )

    client = user_client(access_token)
    payload, err = create_chat_with_initial_request(client, body)
    if err == "invalid_tokens":
        return return_error(
            "BAD_REQUEST",
            "Missing or invalid chat data: tokensToSpend must be a positive number",
        )
    if err or not payload:
        return return_error("INTERNAL_SERVER_ERROR")

    chat_id = payload["chat_id"]
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify(build_chat_detail(client, chat)), HTTPStatus.CREATED


@requester_bp.route("/v1/requester/chats", methods=["GET"])
def list_chats():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)

    chats = (
        client.table("chats")
        .select("*")
        .eq("requester_id", str(user.id))
        .order("created_at", desc=True)
        .execute()
        .data
        or []
    )

    cids = [c["chat_id"] for c in chats]
    totals = token_totals_by_chat(client, cids)
    out = [chat_summary_dict(c, totals.get(c["chat_id"], 0)) for c in chats]
    return jsonify(out), HTTPStatus.OK


@requester_bp.route("/v1/requester/chats/<chatID>", methods=["GET"])
def get_chat(chatID):
    access_token, error = require_access_token()
    if error:
        return error
    _, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    chat = get_chat_or_none(client, chatID)
    if not chat:
        return return_error("NOT_FOUND")

    return jsonify(build_chat_detail(client, chat)), HTTPStatus.OK


@requester_bp.route("/v1/requester/chats/<chatID>/messages", methods=["POST"])
def send_message(chatID):
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    if "message" not in body:
        return return_error(
            "BAD_REQUEST", "Missing or invalid message data: missing field: message"
        )

    client = user_client(access_token)
    if not get_chat_or_none(client, chatID):
        return return_error("NOT_FOUND")

    # supabase-py request builders are dynamically typed; pylint cannot infer chained members.
    # pylint: disable=no-member
    try:
        row = (
            client.table("messages")
            .insert(
                {
                    "chat_id": chatID,
                    "sender_id": str(user.id),
                    "sender_type": "requester",
                    "message": body["message"],
                }
            )
            .execute()
            .data
        )
    except APIError:
        return return_error("FORBIDDEN", "You cannot post to this chat.")
    # pylint: enable=no-member
    if isinstance(row, list):
        row = row[0] if row else None
    if not row:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify(message_dict(row)), HTTPStatus.CREATED


@requester_bp.route("/v1/requester/chats/<chatID>/requests", methods=["POST"])
def add_request(chatID):
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    if "requestText" not in body:
        return return_error(
            "BAD_REQUEST", "Missing or invalid request data: missing field: requestText"
        )

    tokens_raw = body.get("tokensToSpend")
    if tokens_raw is None:
        return return_error(
            "BAD_REQUEST",
            "Missing or invalid request data: tokensToSpend is required",
        )
    try:
        tokens = int(tokens_raw)
    except (TypeError, ValueError):
        return return_error(
            "BAD_REQUEST",
            "Missing or invalid request data: invalid tokensToSpend",
        )
    if tokens <= 0:
        return return_error(
            "BAD_REQUEST",
            "Missing or invalid request data: tokensToSpend must be positive",
        )

    client = user_client(access_token)
    if not get_chat_or_none(client, chatID):
        return return_error("NOT_FOUND")

    # supabase-py request builders are dynamically typed; pylint cannot infer chained members.
    # pylint: disable=no-member
    try:
        row = (
            client.table("requests")
            .insert(
                {
                    "chat_id": chatID,
                    "requester_id": str(user.id),
                    "request_text": body["requestText"],
                    "tokens_to_spend": tokens,
                    "status": "pending",
                }
            )
            .execute()
            .data
        )
    except APIError:
        return return_error(
            "PAYMENT_REQUIRED",
            "You do not have enough tokens to create a new request.",
        )
    # pylint: enable=no-member
    if isinstance(row, list):
        row = row[0] if row else None
    if not row:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify(request_dict(row)), HTTPStatus.CREATED


@requester_bp.route("/v1/requester/chats/<chatID>/close", methods=["POST"])
def close_chat(chatID):
    access_token, error = require_access_token()
    if error:
        return error
    _, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    chat = get_chat_or_none(client, chatID)
    if not chat:
        return return_error("NOT_FOUND")

    try:
        client.table("chats").update(
            {
                "status": "closed",
                "closed_at": datetime.now(UTC).isoformat(),
            }
        ).eq("chat_id", chatID).execute()
    except APIError:
        return return_error("FORBIDDEN")

    return jsonify({"message": "Chat closed"}), HTTPStatus.OK
