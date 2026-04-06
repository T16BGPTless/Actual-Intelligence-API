"""Authentication endpoints."""

from http import HTTPStatus
import uuid
from flask import Blueprint, jsonify, request
from app.routes.helpers import return_error, require_access_token

auth_bp = Blueprint("auth", __name__)

# ------------------- POST /v1/auth/register -------------------
@auth_bp.route("/v1/auth/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    
    # Check for required fields
    required_fields = ["email", "password", "name", "userName"]
    for field in required_fields:
        if field not in body:
            return return_error("BAD_REQUEST", f"Missing or invalid registration data: missing field: {field}")

    # Mocking a Conflict (409)
    if body["email"] == "taken@example.com":
        return return_error("CONFLICT", "An account with this email already exists")

    return jsonify({
        "accessToken": "at_" + uuid.uuid4().hex,
        "user": {
            "email": body["email"],
            "name": body["name"],
            "userName": body["userName"],
            "createdAt": "2026-04-03T10:30:00Z"
        }
    }), HTTPStatus.CREATED

# ------------------- POST /v1/auth/login -------------------
@auth_bp.route("/v1/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}
    
    # Check for specific missing password error
    if "password" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid login data: missing field: password")
    if "email" not in body:
        return return_error("BAD_REQUEST", "Missing or invalid login data: missing field: email")

    # Mocking Unauthorized (401)
    if body["email"] == "wrong@example.com":
        return return_error("UNAUTHORIZED", "Invalid email or password")

    return jsonify({
        "accessToken": "at_" + uuid.uuid4().hex,
        "user": {
            "email": body["email"],
            "name": "Jane Doe",
            "userName": "pro_responder",
            "createdAt": "2026-04-03T10:30:00Z"
        }
    }), HTTPStatus.OK

# ------------------- POST /v1/auth/logout -------------------
@auth_bp.route("/v1/auth/logout", methods=["POST"])
def logout():
    # Verify token exists before logging out
    _, error = require_access_token()
    if error: 
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    return jsonify({"message": "Logged out successfully"}), HTTPStatus.OK

# ------------------- GET /v1/auth/me -------------------
@auth_bp.route("/v1/auth/me", methods=["GET"])
def get_me():
    # This checks the Authorization header
    _, error = require_access_token()
    if error: 
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    # Mock return of the 'User' <--- (WILL HAVE TO CHANGE TO SUPABASE LOGIC)
    return jsonify({
        "email": "user@gptless.au",
        "name": "Current User",
        "userName": "current_user_123",
        "createdAt": "2026-04-03T10:30:00Z"
    }), HTTPStatus.OK