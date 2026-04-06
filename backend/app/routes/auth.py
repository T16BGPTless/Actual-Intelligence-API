"""Authentication endpoints."""

from http import HTTPStatus

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

from app.chat_data import api_ts
from app.config import supabase_email_redirect_to
from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import anon_client, user_client

auth_bp = Blueprint("auth", __name__)


def _user_payload(access_token: str, user) -> dict:
    meta = user.user_metadata or {}
    try:
        client = user_client(access_token)
        prof = (
            client.table("profiles")
            .select("username,display_name,created_at")
            .eq("user_id", str(user.id))
            .maybe_single()
            .execute()
            .data
        )
    except APIError:
        prof = None

    if prof:
        username = prof.get("username") or meta.get("username") or ""
        name = prof.get("display_name") or meta.get("name") or ""
        created = api_ts(prof.get("created_at") or user.created_at)
    else:
        username = meta.get("username") or ""
        name = meta.get("name") or ""
        created = api_ts(user.created_at)

    return {
        "email": user.email,
        "name": name,
        "userName": username,
        "username": username,
        "createdAt": created,
    }


@auth_bp.route("/v1/auth/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}

    required_fields = ["email", "password", "name", "username"]
    for field in required_fields:
        if field not in body:
            return return_error(
                "BAD_REQUEST",
                f"Missing or invalid registration data: missing field: {field}",
            )

    signup_options = {
        "data": {
            "username": body.get("username") or body.get("userName"),
            "name": body["name"],
        }
    }
    redirect_to = supabase_email_redirect_to()
    if redirect_to:
        signup_options["email_redirect_to"] = redirect_to

    try:
        auth_response = anon_client().auth.sign_up(
            {
                "email": body["email"],
                "password": body["password"],
                "options": signup_options,
            }
        )
    except AuthApiError as e:
        msg = (e.message or "").lower()
        if "already" in msg or "registered" in msg:
            return return_error("CONFLICT", "An account with this email already exists")
        return return_error("BAD_REQUEST", e.message or "Registration failed")

    if not auth_response.session:
        try:
            auth_response = anon_client().auth.sign_in_with_password(
                {"email": body["email"], "password": body["password"]}
            )
        except AuthApiError:
            return return_error(
                "FORBIDDEN",
                "Confirm your email address before using the API.",
            )

        if not auth_response.session:
            return return_error(
                "FORBIDDEN",
                "Confirm your email address before using the API.",
            )

    user = auth_response.user
    if not user:
        return return_error("INTERNAL_SERVER_ERROR")

    token = auth_response.session.access_token
    return (
        jsonify(
            {
                "accessToken": token,
                "user": _user_payload(token, user),
            }
        ),
        HTTPStatus.CREATED,
    )


@auth_bp.route("/v1/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}

    if "password" not in body:
        return return_error(
            "BAD_REQUEST", "Missing or invalid login data: missing field: password"
        )
    if "email" not in body:
        return return_error(
            "BAD_REQUEST", "Missing or invalid login data: missing field: email"
        )

    try:
        auth_response = anon_client().auth.sign_in_with_password(
            {"email": body["email"], "password": body["password"]}
        )
    except AuthApiError:
        return return_error("UNAUTHORIZED", "Invalid email or password")

    if not auth_response.session or not auth_response.user:
        return return_error("UNAUTHORIZED", "Invalid email or password")

    token = auth_response.session.access_token
    return (
        jsonify(
            {
                "accessToken": token,
                "user": _user_payload(token, auth_response.user),
            }
        ),
        HTTPStatus.OK,
    )


@auth_bp.route("/v1/auth/logout", methods=["POST"])
def logout():
    access_token, error = require_access_token()
    if error:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    try:
        anon_client().auth.admin.sign_out(access_token, "local")
    except AuthApiError:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    return jsonify({"message": "Logged out successfully"}), HTTPStatus.OK


@auth_bp.route("/v1/auth/me", methods=["GET"])
def get_me():
    access_token, error = require_access_token()
    if error:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    user, error = require_supabase_user(access_token)
    if error:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    return jsonify(_user_payload(access_token, user)), HTTPStatus.OK
