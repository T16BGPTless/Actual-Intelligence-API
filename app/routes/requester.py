"""Requester side endpoints."""

from http import HTTPStatus
import uuid
from flask import Blueprint, jsonify, request
from app.routes.helpers import return_error, require_access_token

requester_bp = Blueprint("requester", __name__)

# ------------------- POST /v1/requester/chats/create -------------------
@requester_bp.route("/v1/requester/chats", methods=["POST"])
def create_chat():
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    if "requestText" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid chat data: missing field: requestText")

    # Mock response matching the 'Chat' schema
    new_chat = {
        "chatID": str(uuid.uuid4().hex[:5]),
        "requesterUsername": "cool_guy",
        "responderUsername": None,
        "status": "open",
        "createdAt": "2025-08-14T10:30:00Z",
        "messages": [],
        "requests": [{
            "requestID": "req_001",
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

    # Mock list of 'ChatSummary'
    chats = [
        {"chatID": "12345", "status": "open", "createdAt": "2025-08-14T10:30:00Z"},
        {"chatID": "54321", "status": "closed", "createdAt": "2025-08-13T09:00:00Z"}
    ]
    return jsonify(chats), HTTPStatus.OK

# ------------------- GET /v1/requester/chats/{chatID} -------------------
@requester_bp.route("/v1/requester/chats/<chatID>", methods=["GET"])
def get_chat(chatID):
    _, error = require_access_token()
    if error: return error

    if chatID == "404": # Mocking a not found
        return return_error("NOT_FOUND")

    return jsonify({"chatID": chatID, "status": "open", "messages": [], "requests": []}), HTTPStatus.OK

# ------------------- POST /v1/requester/chats/{chatID}/messages -------------------
@requester_bp.route("/v1/requester/chats/<chatID>/messages", methods=["POST"])
def send_message(chatID):
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    if "message" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid message data: missing field: message")

    return jsonify({
        "messageID": "msg_" + uuid.uuid4().hex[:4],
        "senderType": "requester",
        "message": body["message"],
        "createdAt": "2025-08-14T10:35:00Z"
    }), HTTPStatus.CREATED

# ------------------- POST /v1/requester/chats/close/{chatID} -------------------
@requester_bp.route("/v1/requester/chats/close/<chatID>", methods=["POST"])
def close_chat(chatID):
    _, error = require_access_token()
    if error: return error

    return "", HTTPStatus.OK