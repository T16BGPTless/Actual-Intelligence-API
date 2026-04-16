"""Responder endpoints."""

from http import HTTPStatus
from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from app.chat_data import build_chat_detail, get_chat_or_none, chat_summary_dict
from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import user_client

responder_bp = Blueprint("responder", __name__)

@responder_bp.route("/v1/responder/chats", methods=["GET"])
def browse_chats():
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    client = user_client(access_token)
    try:
        q = client.table("chats").select("*").eq("status", "open")
        data = q.order("created_at", desc=False).execute().data or []
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify([chat_summary_dict(client, c) for c in data]), HTTPStatus.OK

@responder_bp.route("/v1/responder/chats/claimed", methods=["GET"])
def claimed_chats():
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    client = user_client(access_token)
    try:
        q = client.table("chats").select("*").eq("responder_id", str(user.id))
        data = q.order("created_at", desc=False).execute().data or []
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")
        
    return jsonify([chat_summary_dict(client, c) for c in data]), HTTPStatus.OK

@responder_bp.route("/v1/responder/chats/<chat_id>/claim", methods=["POST"])
def claim_chat(chat_id):
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not title:
        return return_error("BAD_REQUEST", "Missing title")
        
    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
        
    if chat["status"] != "open" or chat["claim_state"] != "unclaimed":
        return return_error("BAD_REQUEST", "Chat is not available")
        
    try:
        client.table("chats").update({
            "status": "active",
            "claim_state": "claimed",
            "responder_id": str(user.id),
            "title": title
        }).eq("chat_id", chat_id).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")
    
    return jsonify({"message": "Chat successfully claimed."}), HTTPStatus.OK

@responder_bp.route("/v1/responder/chats/<chat_id>/messages", methods=["POST"])
def post_message(chat_id):
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    body = request.get_json(silent=True) or {}
    msg_text = body.get("message")
    if not msg_text:
        return return_error("BAD_REQUEST", "Missing message")
        
    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
        
    if str(chat["responder_id"]) != str(user.id):
        return return_error("FORBIDDEN", "Forbidden")
        
    try:
        client.table("messages").insert({
            "chat_id": chat_id,
            "sender_type": "responder",
            "message": msg_text
        }).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")
    
    return jsonify({"message": "Message sent."}), HTTPStatus.CREATED

@responder_bp.route("/v1/responder/chats/<chat_id>", methods=["GET"])
def get_chat_detail(chat_id):
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    body = request.get_json(silent=True) or {}
    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
        
    if str(chat["responder_id"]) != str(user.id) and chat["status"] != "open":
        return return_error("FORBIDDEN", "Forbidden")
        
    return jsonify(build_chat_detail(client, chat)), HTTPStatus.OK