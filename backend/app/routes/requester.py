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
        return return_error("INTERNAL_SERVER_ERROR", "Unable to create chat")
        
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
    sclient = service_client()
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "Forbidden")
    if chat["status"] != "claimed":
        return return_error("BAD_REQUEST", "Chat is not claimed")
        
    tokens = body.get("tokensToSpend", 0)
    
    try:
        if tokens > 0:
            req_account = sclient.table("accounts").select("account_id").eq("created_by", str(user.id)).maybe_single().execute().data
            if req_account:
                acc_id = req_account["account_id"]
                cur = sclient.table("token_balances").select("balance").eq("account_id", acc_id).maybe_single().execute().data
                cur_bal = int((cur or {}).get("balance") or 0)
                if cur_bal < tokens:
                    return return_error("BAD_REQUEST", "invalid_tokens")
                sclient.table("token_balances").update({"balance": cur_bal - tokens}).eq("account_id", acc_id).execute()
                sclient.table("token_transactions").insert({
                    "account_id": acc_id,
                    "txn_type": "spend",
                    "amount": -tokens,
                    "chat_id": chat_id,
                    "created_by": str(user.id)
                }).execute()
            client.table("chats").update({"tokens_spent": chat.get("tokens_spent", 0) + tokens}).eq("chat_id", chat_id).execute()
            
        client.table("messages").insert({
            "chat_id": chat_id,
            "sender_id": str(user.id),
            "sender_type": "requester",
            "message": msg_text,
            "tokens": tokens
        }).execute()
    except APIError as e:
        return return_error("INTERNAL_SERVER_ERROR")
    
    return jsonify({
        "message_id": "temp",
        "senderType": "requester",
        "message": msg_text,
        "tokens": tokens,
        "createdAt": "2026-04-16T12:00:00Z"
    }), HTTPStatus.CREATED

@requester_bp.route("/v1/requester/chats/<chat_id>/review", methods=["POST"])
def review_chat(chat_id):
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    body = request.get_json(silent=True) or {}
    rating = body.get("rating")
    
    client = user_client(access_token)
    sclient = service_client()
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "Forbidden")
    if chat["status"] != "closing":
        return return_error("BAD_REQUEST", "Chat is not closing")
        
    upd = {"status": "closed", "resolved": body.get("resolved", True)}
    if rating:
        upd["rating"] = rating
        
    try:
        # Payout tokens to responder
        responder_id = chat.get("responder_id")
        tokens_spent = int(chat.get("tokens_spent") or 0)
        
        if responder_id and tokens_spent > 0:
            res_account = sclient.table("accounts").select("account_id").eq("created_by", responder_id).maybe_single().execute().data
            if res_account:
                acc_id = res_account["account_id"]
                # get current balance
                cur = sclient.table("token_balances").select("balance").eq("account_id", acc_id).maybe_single().execute().data
                cur_bal = int((cur or {}).get("balance") or 0)
                
                sclient.table("token_balances").update({"balance": cur_bal + tokens_spent}).eq("account_id", acc_id).execute()
                sclient.table("token_transactions").insert({
                    "account_id": acc_id,
                    "txn_type": "adjustment",
                    "amount": tokens_spent,
                    "chat_id": chat_id,
                    "created_by": str(user.id)
                }).execute()

        client.table("chats").update(upd).eq("chat_id", chat_id).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")
    
    return jsonify({"message": "Chat successfully closed."}), HTTPStatus.OK

