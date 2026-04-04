"""Authentication endpoints."""

from http import HTTPStatus
import uuid
from flask import Blueprint, jsonify, request
from app.routes.helpers import return_error

auth_bp = Blueprint("auth", __name__)

# ------------------- POST /v1/auth/register -------------------
@auth_bp.route("/v1/auth/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}
    
    # Check for required fields based on the RegisterRequest schema
    required_fields = ["email", "password", "name", "userName"]
    for field in required_fields:
        if field not in body:
            return return_error("BAD_REQUEST", f"Missing or invalid registration data: missing field: {field}")

    # Mocking a Conflict (409)
    if body["email"] == "taken@example.com":
        return return_error("CONFLICT", "An account with this email already exists")

    # Success (201 Created)
    return jsonify({
        "accessToken": uuid.uuid4().hex,
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
    if "email" not in body or "password" not in body:
        return return_error("BAD_REQUEST", "Missing email or password")

    return jsonify({
        "accessToken": uuid.uuid4().hex,
        "user": {
            "email": body["email"],
            "name": "Jane Doe",
            "userName": "pro_responder",
            "createdAt": "2026-04-03T10:30:00Z"
        }
    }), HTTPStatus.OK