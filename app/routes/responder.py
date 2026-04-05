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

    categories = request.args.get("categories")

    # Mock response matching ChatSummary
    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Filter by responder_id)
    chats = [
        {
            "chatID": "12345", 
            "title": "website design", 
            "category": "development", 
            "status": "open", 
            "tokens": 30, 
            "createdAt": "2025-08-14T10:30:00Z"
        }
    ]
    return jsonify(chats), HTTPStatus.OK

# ------------------- GET /v1/responder/chats/unclaimed -------------------
@responder_bp.route("/v1/responder/chats/unclaimed", methods=["GET"])
def list_unclaimed_chats():
    _, error = require_access_token()
    if error: return error

    categories = request.args.get("categories")

    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Select where responder_id IS NULL)
    unclaimed = [
        {
            "chatID": "e4f0d", 
            "title": "Bug in React App", 
            "category": "development", 
            "status": "open", 
            "tokens": 50, 
            "createdAt": "2026-04-05T12:00:00Z"
        }
    ]
    return jsonify(unclaimed), HTTPStatus.OK

# ------------------- GET /v1/responder/chats/{chatID} -------------------
# Removed 'int:' to allow hex strings like 'e4f0d'
@responder_bp.route("/v1/responder/chats/<chatID>", methods=["GET"])
def get_chat(chatID):
    _, error = require_access_token()
    if error: return error

    # Mocking not found
    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Check if row exists)
    if chatID == "nonexistent":
        return return_error("NOT_FOUND", "The requested resource was not found")

    return jsonify({
        "chatID": chatID,
        "title": "Sample Chat",
        "category": "writing",
        "status": "open",
        "messages": [],
        "requests": []
    }), HTTPStatus.OK

# ------------------- POST /v1/responder/chats/{chatID}/claim -------------------
@responder_bp.route("/v1/responder/chats/<chatID>/claim", methods=["POST"])
def claim_chat(chatID):
    _, error = require_access_token()
    if error: return error

    # Mocking already claimed
    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Update responder_id if currently NULL)
    if chatID == "12002": 
        return return_error("CONFLICT", "This chat has already been claimed")

    # YAML expects 200 OK for successful claim
    return jsonify({
        "chatID": chatID,
        "title": "Claimed Chat",
        "status": "claimed",
        "messages": [],
        "requests": []
    }), HTTPStatus.OK

# ------------------- POST /v1/responder/chats/{chatID}/messages -------------------
@responder_bp.route("/v1/responder/chats/<chatID>/messages", methods=["POST"])
def send_message(chatID):
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    if "message" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid message data: missing field: message")

    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Insert into messages table)
    return jsonify({
        "messageID": "msg_" + uuid.uuid4().hex[:6],
        "senderType": "responder",
        "message": body["message"],
        "createdAt": "2026-04-05T14:00:00Z"
    }), HTTPStatus.CREATED

# ------------------- POST /v1/responder/chats/{chatID}/fulfill-request -------------------
@responder_bp.route("/v1/responder/chats/<chatID>/fulfill-request", methods=["POST"])
def fulfill_request(chatID):
    _, error = require_access_token()
    if error: return error

    body = request.get_json(silent=True) or {}
    if "responseText" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid fulfillment data: missing field: responseText")

    # Mocking Conflict
    # <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC: Check if active request exists)
    if chatID == "empty_chat": 
        return return_error("CONFLICT", "There is no active request to fulfill")

    return jsonify({
        "fulfillmentID": "full_" + uuid.uuid4().hex[:6],
        "requestID": "req_abc",
        "responseText": body["responseText"],
        "createdAt": "2026-04-05T14:10:00Z"
    }), HTTPStatus.CREATED