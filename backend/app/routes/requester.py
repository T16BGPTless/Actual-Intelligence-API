"""Requester endpoints."""

from http import HTTPStatus
from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from app.chat_data import build_chat_detail, create_chat_with_initial_request, get_chat_or_none, categories_from_flask_arg, chat_summary_dict
from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import service_client, user_client

requester_bp = Blueprint("requester", __name__)

@requester_bp.route("/v1/requester/chats", methods=["POST"])
def create_chat():
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
    
    body = request.get_json(silent=True) or {}
    for req in ["requestText", "tokensToSpend"]:
        if req not in body:
            return return_error("BAD_REQUEST", f"Missing field: {req}")
            
    client = user_client(access_token)
    payload, err = create_chat_with_initial_request(client, body)
    if err == "invalid_tokens":
        return return_error("BAD_REQUEST", "Invalid tokensToSpend")
    if err:
        return return_error("BAD_REQUEST", err)
        
    return jsonify({
        "chatID": payload["chat_id"],
        "message": "Chat successfully created."
    }), HTTPStatus.CREATED

@requester_bp.route("/v1/requester/chats", methods=["GET"])
def get_user_chats():
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    client = user_client(access_token)
    cats = categories_from_flask_arg(request.args.getlist("category"), request.args.get("category"))
    status = request.args.get("status")
    
    q = client.table("chats").select("*").eq("requester_id", str(user.id))
    if cats:
        q = q.in_("category", cats)
    if status in ["open", "active", "completed"]:
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
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "Forbidden")
        
    return jsonify(build_chat_detail(client, chat)), HTTPStatus.OK

@requester_bp.route("/v1/requester/chats/<chat_id>/messages", methods=["POST"])
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
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "Forbidden")
    if chat["status"] != "active":
        return return_error("BAD_REQUEST", "Chat is not active")
        
    tokens = body.get("tokens", 0)
    
    try:
        if tokens > 0:
            client.table("chats").update({"tokens_spent": chat.get("tokens_spent", 0) + tokens}).eq("chat_id", chat_id).execute()
            
        client.table("messages").insert({
            "chat_id": chat_id,
            "sender_type": "requester",
            "message": msg_text,
            "tokens": tokens
        }).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")
    
    return jsonify({"message": "Message sent successfully."}), HTTPStatus.CREATED

@requester_bp.route("/v1/requester/chats/<chat_id>/resolve", methods=["POST"])
def resolve_chat(chat_id):
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    body = request.get_json(silent=True) or {}
    rating = body.get("rating")
    
    client = user_client(access_token)
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORIDDEN", "Forbidden")
    if chat["status"] != "active":
        return return_error("BAD_REQUEST", "Chat is not active")
        
    upd = {"status": "completed", "resolved": True}
    if rating:
        upd["rating"] = rating
        
    try:
        client.table("chats").update(upd).eq("chat_id", chat_id).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")
    
    return jsonify({"message": "Chat marked as completed."}), HTTPStatus.OK
