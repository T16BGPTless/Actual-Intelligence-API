"""Requester side endpoints."""

from http import HTTPStatus
import uuid
from flask import Blueprint, jsonify, request
from app.routes.helpers import return_error, require_access_token

requester_bp = Blueprint("requester", __name__)

# ------------------- POST /v1/requester/chats -------------------
@requester_bp.route("/v1/requester/chats", methods=["POST"])
def create_chat():
    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Validate token and get user_id)
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    if "requestText" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid chat data: missing field: requestText")

    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Insert into 'chats' and 'requests' tables)
    new_chat = {
        "chatID": str(uuid.uuid4().hex[:5]),
        "title": body.get("title", "New Request"),
        "category": body.get("category", "general"),
        "requesterUsername": "cool_guy", # <--- (GET FROM SUPABASE JOIN)
        "responderUsername": None,
        "status": "open",
        "tokens": body.get("tokensToSpend", 0),
        "createdAt": "2025-08-14T10:30:00Z",
        "messages": [],
        "requests": [{
            "requestID": "req_" + uuid.uuid4().hex[:4],
            "requestText": body.get("requestText"),
            "status": "pending",
            "tokensSpent": body.get("tokensToSpend", 0),
            "createdAt": "2025-08-14T10:30:00Z"
        }]
    }
    return jsonify(new_chat), HTTPStatus.CREATED

# ------------------- GET /v1/requester/chats -------------------
@requester_bp.route("/v1/requester/chats", methods=["GET"])
def list_chats():
    _, error = require_access_token()
    if error: return error

    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Select chats where requester_id = current_user)
    chats = [
        {
            "chatID": "12345", 
            "title": "website design", 
            "category": "development", 
            "status": "open", 
            "tokens": 30, 
            "createdAt": "2025-08-14T10:30:00Z"
        },
        {
            "chatID": "54321", 
            "title": "poem request", 
            "category": "writing", 
            "status": "closed", 
            "tokens": 40, 
            "createdAt": "2025-08-13T09:00:00Z"
        }
    ]
    return jsonify(chats), HTTPStatus.OK

# ------------------- GET /v1/requester/chats/{chatID} -------------------
@requester_bp.route("/v1/requester/chats/<chatID>", methods=["GET"])
def get_chat(chatID):
    _, error = require_access_token()
    if error: return error

    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Fetch full chat details, messages, and requests)
    if chatID == "404": 
        return return_error("NOT_FOUND")

    return jsonify({
        "chatID": chatID, 
        "title": "Existing Chat",
        "status": "open", 
        "messages": [], 
        "requests": []
    }), HTTPStatus.OK

# ------------------- POST /v1/requester/chats/{chatID}/messages -------------------
@requester_bp.route("/v1/requester/chats/<chatID>/messages", methods=["POST"])
def send_message(chatID):
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    if "message" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid message data: missing field: message")

    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Insert into 'messages' table)
    return jsonify({
        "messageID": "msg_" + uuid.uuid4().hex[:4],
        "senderType": "requester",
        "message": body["message"],
        "createdAt": "2026-04-05T10:35:00Z"
    }), HTTPStatus.CREATED

# ------------------- POST /v1/requester/chats/{chatID}/requests -------------------
@requester_bp.route("/v1/requester/chats/<chatID>/requests", methods=["POST"])
def add_request(chatID):
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    if "requestText" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid request data: missing field: requestText")

    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Insert into 'requests' table linked to chatID)
    return jsonify({
        "requestID": "req_" + uuid.uuid4().hex[:4],
        "requestText": body["requestText"],
        "status": "pending",
        "tokensSpent": body.get("tokensToSpend", 0),
        "createdAt": "2026-04-05T11:00:00Z"
    }), HTTPStatus.CREATED

# ------------------- POST /v1/requester/chats/{chatID}/close -------------------
@requester_bp.route("/v1/requester/chats/<chatID>/close", methods=["POST"])
def close_chat(chatID):
    _, error = require_access_token()
    if error: return error

    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Update chat status to 'closed')
    return jsonify({"message": "Chat closed"}), HTTPStatus.OK