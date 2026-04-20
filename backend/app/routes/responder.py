"""Responder endpoints."""

from http import HTTPStatus
from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from app.chat_data import (
    build_chat_detail,
    get_chat_or_none,
    chat_summary_dict,
    message_dict,
)
from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import user_client, service_client

responder_bp = Blueprint("responder", __name__)


@responder_bp.route("/v1/responder/chats", methods=["GET"])
def claimed_chats():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    try:
        q = (
            client.table("chats")
            .select("*")
            .eq("responder_id", str(user.id))
            .neq("requester_id", str(user.id))
        )
        data = q.order("created_at", desc=False).execute().data or []
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify([chat_summary_dict(client, c) for c in data]), HTTPStatus.OK


@responder_bp.route("/v1/responder/chats/unclaimed", methods=["GET"])
def browse_chats():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = user_client(access_token)
    try:
        q = (
            client.table("chats")
            .select("*")
            .eq("status", "open")
            .neq("requester_id", str(user.id))
        )
        data = q.order("created_at", desc=False).execute().data or []
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify([chat_summary_dict(client, c) for c in data]), HTTPStatus.OK


@responder_bp.route("/v1/responder/chats/<chat_id>", methods=["GET"])
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

    if str(chat["responder_id"]) != str(user.id) and chat["status"] != "open":
        return return_error("FORBIDDEN", "You do not have access to this content")

    return jsonify(build_chat_detail(client, chat)), HTTPStatus.OK


@responder_bp.route("/v1/responder/chats/<chat_id>/claim", methods=["POST"])
def claim_chat(chat_id):
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not title:
        return return_error(
            "BAD_REQUEST", "Missing or invalid claim data: missing field: title"
        )

    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        s_client = service_client()
        s_chat = get_chat_or_none(s_client, chat_id)
        if s_chat and (
            s_chat["status"] != "open" or s_chat["claim_state"] != "unclaimed"
        ):
            return return_error("CONFLICT", "This chat has already been claimed")
        return return_error("NOT_FOUND", "Not Found")

    if chat["status"] != "open" or chat["claim_state"] != "unclaimed":
        return return_error("CONFLICT", "This chat has already been claimed")

    try:
        res = (
            client.table("chats")
            .update(
                {
                    "status": "claimed",
                    "claim_state": "claimed",
                    "responder_id": str(user.id),
                    "title": title,
                }
            )
            .eq("chat_id", chat_id)
            .eq("status", "open")
            .eq("claim_state", "unclaimed")
            .is_("responder_id", "null")
            .execute()
        )
        if not getattr(res, "data", None):
            return return_error("CONFLICT", "This chat has already been claimed")
    except APIError as e:
        msg = getattr(e, "message", "") or ""
        code = getattr(e, "code", "") or ""

        if "policy" in msg.lower() or code == "42501":
            return return_error("FORBIDDEN", "You do not have access to this content")
        if (
            "duplicate" in msg.lower()
            or code == "23505"
            or "already claimed" in msg.lower()
        ):
            return return_error("CONFLICT", "This chat has already been claimed")

        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify({"message": "Chat successfully claimed."}), HTTPStatus.OK


@responder_bp.route("/v1/responder/chats/<chat_id>/messages", methods=["POST"])
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

    if str(chat["responder_id"]) != str(user.id):
        return return_error("FORBIDDEN", "You do not have access to this content")
    if chat["status"] != "claimed":
        return return_error("BAD_REQUEST", "Chat is not in claimed state")

    try:
        res = (
            client.table("messages")
            .insert(
                {
                    "chat_id": chat_id,
                    "sender_id": str(user.id),
                    "sender_type": "responder",
                    "message": msg_text,
                }
            )
            .execute()
        )

        msg_row = (
            res.data[0]
            if getattr(res, "data", None)
            else {
                "sender_type": "responder",
                "message": msg_text,
                "tokens": 0,
                "created_at": "2026-04-16T12:00:00Z",
            }
        )
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify(message_dict(msg_row)), HTTPStatus.CREATED


@responder_bp.route("/v1/responder/chats/<chat_id>/close", methods=["POST"])
def close_chat(chat_id):
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

    if str(chat["responder_id"]) != str(user.id):
        return return_error("FORBIDDEN", "You do not have access to this content")

    if chat["status"] != "claimed":
        return return_error("CONFLICT", "There is no active request to fulfill")

    try:
        client.table("chats").update({"status": "closing"}).eq(
            "chat_id", chat_id
        ).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify({"message": "Chat successfully closed."}), HTTPStatus.OK
