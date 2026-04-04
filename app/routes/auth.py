"""Authentication methods."""

from http import HTTPStatus
import uuid
from flask import Blueprint, jsonify, request
from app.routes.helpers import (
    return_error,
    require_access_token
)

auth_bp = Blueprint("auth", __name__)


# ------------------- POST /v1/auth/login -------------------
@auth_bp.route("/v1/auth/login", methods=["POST"])
def login():
    """Log in to an existing account."""
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        missing = "password" if email else "email" if password else "email and password"
        return return_error(
            "BAD_REQUEST", 
            f"Missing or invalid login data: missing field: {missing}"
        )

    if email != "guy@example.com" or password != "mySecurePassword123":
        return return_error("UNAUTHORIZED", "Invalid email or password")

    # Generate mock access token
    access_token = uuid.uuid4().hex

    # Return AuthResponse schema
    return jsonify({
        "accessToken": access_token,
        "user": {
            "userName": "cool_guy",
            "name": "Guy",
            "email": email,
            "createdAt": "2026-04-03T10:30:00Z"
        }
    }), HTTPStatus.OK


# ------------------- POST /v1/auth/logout -------------------
@auth_bp.route("/v1/auth/logout", methods=["POST"])
def logout():
    """Logs out the currently authenticated user."""
    _, error = require_access_token()
    if error is not None:
        return error
    
    return jsonify({"message": "Logged out successfully"}), HTTPStatus.OK


# ------------------- GET /v1/auth/me -------------------
@auth_bp.route("/v1/auth/me", methods=["GET"])
def get_me():
    """Returns the currently authenticated user's account details."""
    token, error = require_access_token()
    if error is not None:
        return error

    # Mock DB fetch using the token
    user_data = {
        "userName": "cool_guy",
        "name": "Guy",
        "email": "guy@example.com",
        "createdAt": "2026-04-03T10:30:00Z"
    }

    return jsonify(user_data), HTTPStatus.OK