"""Responder side endpoints."""

from http import HTTPStatus
import uuid
from flask import Blueprint, jsonify, request
from app.routes.helpers import return_error, require_access_token

responder_bp = Blueprint("responder", __name__)

# ------------------- GET /v1/responder/chats -------------------
@responder_bp.route("/v1/responder/chats", methods=["GET"])
def list_chats():
    _, error = require_access_token()
    if error: return error

    # Capturing query params from your spec
    status_filter = request.args.get("status")
    claimed_filter = request.args.get("claimed")

    # Mock response array of ChatSummary
    chats = [
        {"chatID": "12001", "status": "unclaimed", "createdAt": "2025-08-14T10:30:00Z"},
        {"chatID": "12002", "status": "claimed", "createdAt": "2025-08-14T11:00:00Z"}
    ]
    return jsonify(chats), HTTPStatus.OK

# ------------------- POST /v1/responder/chats/claim/{chatID} -------------------
@responder_bp.route("/v1/responder/chats/claim/<chatID>", methods=["POST"])
def claim_chat(chatID):
    _, error = require_access_token()
    if error: return error

    # Mocking a 404
    if chatID == "nonexistent":
        return return_error("NOT_FOUND")

    # Mocking a 409 Conflict (Already claimed)
    if chatID == "12002":
        return return_error("CONFLICT", "This chat has already been claimed")

    # Success (201 Created)
    return jsonify({
        "chatID": chatID,
        "requesterUsername": "cool_guy",
        "responderUsername": "pro_responder",
        "status": "claimed",
        "createdAt": "2025-08-14T10:30:00Z",
        "messages": [],
        "requests": []
    }), HTTPStatus.CREATED

# ------------------- POST /v1/responder/chats/{chatID}/messages -------------------
@responder_bp.route("/v1/responder/chats/<chatID>/messages", methods=["POST"])
def send_message(chatID):
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    if "message" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid message data: missing field: message")

    return jsonify({
        "messageID": "msg_" + uuid.uuid4().hex[:4],
        "senderType": "responder",
        "message": body["message"],
        "createdAt": "2025-08-14T11:05:00Z"
    }), HTTPStatus.CREATED

# ------------------- POST /v1/responder/chats/{chatID}/fulfill-request -------------------
@responder_bp.route("/v1/responder/chats/<chatID>/fulfill-request", methods=["POST"])
def fulfill_request(chatID):
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    
    # 400 Bad Request
    if "responseText" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid fulfillment data: missing field: responseText")

    # 409 Conflict (No active request) - Mocking with a specific ID
    if chatID == "empty_chat":
        return return_error("CONFLICT", "There is no active request to fulfill")

    return jsonify({
        "fulfillmentID": "full_" + uuid.uuid4().hex[:4],
        "requestID": "req_123",
        "responseText": body["responseText"],
        "createdAt": "2025-08-14T11:10:00Z"
    }), HTTPStatus.CREATED

# ------------------- GET /v1/responder/chats/{chatID} -------------------
@responder_bp.route("/v1/responder/chats/<chatID>", methods=["GET"])
def get_chat(chatID):
    _, error = require_access_token()
    if error: return error

    return jsonify({
        "chatID": chatID,
        "requesterUsername": "user1",
        "responderUsername": "responder1",
        "status": "open",
        "createdAt": "2025-08-14T10:30:00Z",
        "messages": [],
        "requests": []
    }), HTTPStatus.OK