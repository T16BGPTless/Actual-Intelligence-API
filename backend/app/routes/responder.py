"""Responder side endpoints."""

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from app.chat_data import (
    api_ts,
    build_chat_detail,
    categories_from_flask_arg,
    chat_summary_dict,
    fulfill_request_rpc,
    get_chat_or_none,
    message_dict,
    token_totals_by_chat,
)
from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import user_client

responder_bp = Blueprint("responder", __name__)


@responder_bp.route("/v1/responder/chats", methods=["GET"])
def list_chats():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    raw = categories_from_flask_arg(
        request.args.getlist("categories"), request.args.get("categories")
    )

    q = client.table("chats").select("*").eq("responder_id", str(user.id))
    if raw:
        q = q.in_("category", raw)
    chats = q.order("created_at", desc=True).execute().data or []

    cids = [c["chat_id"] for c in chats]
    totals = token_totals_by_chat(client, cids)
    out = [chat_summary_dict(c, totals.get(c["chat_id"], 0)) for c in chats]
    return jsonify(out), HTTPStatus.OK


@responder_bp.route("/v1/responder/chats/unclaimed", methods=["GET"])
def list_unclaimed_chats():
    access_token, error = require_access_token()
    if error:
        return error
    _, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    raw = categories_from_flask_arg(
        request.args.getlist("categories"), request.args.get("categories")
    )

    q = (
        client.table("chats")
        .select("*")
        .is_("responder_id", None)
        .eq("claim_state", "unclaimed")
        .eq("status", "open")
    )
    if raw:
        q = q.in_("category", raw)
    chats = q.order("created_at", desc=True).execute().data or []

    cids = [c["chat_id"] for c in chats]
    totals = token_totals_by_chat(client, cids)
    out = [chat_summary_dict(c, totals.get(c["chat_id"], 0)) for c in chats]
    return jsonify(out), HTTPStatus.OK


@responder_bp.route("/v1/responder/chats/<chatID>", methods=["GET"])
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
        return return_error("NOT_FOUND", "The requested resource was not found")

    return jsonify(build_chat_detail(client, chat)), HTTPStatus.OK


@responder_bp.route("/v1/responder/chats/<chatID>/claim", methods=["POST"])
def claim_chat(chatID):
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    chat = get_chat_or_none(client, chatID)
    if not chat:
        return return_error("NOT_FOUND", "The requested resource was not found")

    if chat.get("responder_id"):
        return return_error("CONFLICT", "This chat has already been claimed")

    if chat.get("claim_state") != "unclaimed" or chat.get("status") != "open":
        return return_error("BAD_REQUEST", "Chat cannot be claimed")

    try:
        updated = (
            client.table("chats")
            .update({"responder_id": str(user.id), "claim_state": "claimed"})
            .eq("chat_id", chatID)
            .is_("responder_id", None)
            .select("*")
            .execute()
            .data
        )
    except APIError as e:
        if getattr(e, "code", None) == "42501" or (
            e.message and "permission" in e.message.lower()
        ):
            return return_error("FORBIDDEN", "You do not have access to this content")
        return return_error("INTERNAL_SERVER_ERROR")

    if not updated:
        return return_error("CONFLICT", "This chat has already been claimed")

    refreshed = updated[0]
    return jsonify(build_chat_detail(client, refreshed)), HTTPStatus.OK


@responder_bp.route("/v1/responder/chats/<chatID>/messages", methods=["POST"])
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
                    "sender_type": "responder",
                    "message": body["message"],
                }
            )
            .select("message_id,sender_type,message,created_at")
            .single()
            .execute()
            .data
        )
    except APIError:
        return return_error("FORBIDDEN", "You do not have access to this content")
    # pylint: enable=no-member

    return jsonify(message_dict(row)), HTTPStatus.CREATED


@responder_bp.route("/v1/responder/chats/<chatID>/fulfill-request", methods=["POST"])
def fulfill_request(chatID):
    access_token, error = require_access_token()
    if error:
        return error
    _, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    if "responseText" not in body:
        return return_error(
            "BAD_REQUEST",
            "Missing or invalid fulfillment data: missing field: responseText",
        )

    client = user_client(access_token)
    if not get_chat_or_none(client, chatID):
        return return_error("NOT_FOUND")

    payload, err = fulfill_request_rpc(client, chatID, body)
    if err == "no_active_request":
        return return_error("CONFLICT", "There is no active request to fulfill")
    if err or not payload:
        return return_error("INTERNAL_SERVER_ERROR")

    try:
        row = (
            client.table("fulfillments")
            .select("fulfillment_id,request_id,response_text,created_at")
            .eq("fulfillment_id", payload["fulfillment_id"])
            .single()
            .execute()
            .data
        )
    except APIError:
        row = None

    if not row:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify(
        {
            "fulfillmentID": row["fulfillment_id"],
            "requestID": row["request_id"],
            "responseText": row["response_text"],
            "createdAt": api_ts(row["created_at"]),
        }
    ), HTTPStatus.CREATED
