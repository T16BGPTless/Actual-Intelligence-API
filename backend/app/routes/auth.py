"""Authentication endpoints."""

from http import HTTPStatus
from datetime import UTC, datetime

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

from app.chat_data import api_ts
from app.config import supabase_email_redirect_to
from app.routes.helpers import require_access_token, require_supabase_user, return_error
from app.supabase_client import anon_client, service_client, user_client

auth_bp = Blueprint("auth", __name__)
ACTIVE_ROLES = {"requester", "responder"}


def _missing_field_error(scope: str, field: str):
    return return_error(
        "BAD_REQUEST",
        f"Missing or invalid {scope} data: missing field: {field}",
    )


def _auth_success_response(auth_response, status_code: HTTPStatus):
    user = auth_response.user
    session = auth_response.session
    if not user or not session:
        return return_error("INTERNAL_SERVER_ERROR")

    token = session.access_token
    _touch_last_online(token, str(user.id))
    return (
        jsonify(
            {
                "accessToken": token,
                "user": _user_payload(token, user),
            }
        ),
        status_code,
    )


def _touch_last_online(access_token: str, user_id: str) -> None:
    try:
        timestamp = datetime.now(UTC).isoformat()
        user_client(access_token).table("profiles").update(
            {"last_online_at": timestamp}
        ).eq("user_id", user_id).execute()
    except Exception:  # pragma: no cover - non-critical best-effort update
        # Do not block auth success responses on non-critical profile timestamp updates.
        return


def _user_payload(access_token: str, user) -> dict:
    meta = user.user_metadata or {}
    try:
        client = user_client(access_token)
        prof = (
            client.table("profiles")
            .select("username,display_name,created_at,last_online_at")
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
        last_online = api_ts(prof.get("last_online_at"))
    else:
        username = meta.get("username") or ""
        name = meta.get("name") or ""
        created = api_ts(user.created_at)
        last_online = None

    return {
        "email": user.email,
        "name": name,
        "username": username,
        "createdAt": created,
        "lastOnline": last_online,
    }


def _get_active_role(user_id: str) -> str:
    rows = (
        service_client()
        .table("user_roles")
        .select("role")
        .eq("user_id", user_id)
        .in_("role", list(ACTIVE_ROLES))
        .execute()
        .data
        or []
    )
    role_set = {r.get("role") for r in rows if r.get("role")}
    if "responder" in role_set:
        return "responder"
    return "requester"


def _set_active_role(user_id: str, role: str) -> None:
    client = service_client()
    client.table("user_roles").delete().eq("user_id", user_id).in_(
        "role", list(ACTIVE_ROLES)
    ).execute()
    client.table("user_roles").insert({"user_id": user_id, "role": role}).execute()


@auth_bp.route("/v1/auth/register", methods=["POST"])
def register():
    body = request.get_json(silent=True) or {}

    required_fields = ["email", "password", "name", "username"]
    for field in required_fields:
        if field not in body:
            return _missing_field_error("registration", field)

    signup_options = {
        "data": {
            "username": body["username"],
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

    signin_fallback_error = return_error(
        "FORBIDDEN",
        "Registration succeeded but automatic sign-in failed.",
    )
    if not auth_response.session:
        user = auth_response.user
        if not user:
            return return_error("INTERNAL_SERVER_ERROR")

        # If email confirmations are enabled upstream, force-confirm and continue login.
        try:
            service_client().auth.admin.update_user_by_id(
                str(user.id),
                {"email_confirm": True},
            )
        except AuthApiError:
            return return_error("INTERNAL_SERVER_ERROR", "Registration failed")

        try:
            auth_response = anon_client().auth.sign_in_with_password(
                {"email": body["email"], "password": body["password"]}
            )
        except AuthApiError:
            return signin_fallback_error

        if not auth_response.session:
            return signin_fallback_error

    return _auth_success_response(auth_response, HTTPStatus.CREATED)


@auth_bp.route("/v1/auth/login", methods=["POST"])
def login():
    body = request.get_json(silent=True) or {}

    if "email" not in body:
        return _missing_field_error("login", "email")
    if "password" not in body:
        return _missing_field_error("login", "password")

    try:
        auth_response = anon_client().auth.sign_in_with_password(
            {"email": body["email"], "password": body["password"]}
        )
    except AuthApiError:
        return return_error("UNAUTHORIZED", "Invalid email or password")

    if not auth_response.session or not auth_response.user:
        return return_error("UNAUTHORIZED", "Invalid email or password")

    return _auth_success_response(auth_response, HTTPStatus.OK)


@auth_bp.route("/v1/auth/logout", methods=["POST"])
def logout():
    access_token, error = require_access_token()
    if error:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    try:
        service_client().auth.admin.sign_out(access_token, "local")
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


@auth_bp.route("/v1/auth/role", methods=["GET"])
def get_role():
    access_token, error = require_access_token()
    if error:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    user, error = require_supabase_user(access_token)
    if error:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    try:
        role = _get_active_role(str(user.id))
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify({"role": role}), HTTPStatus.OK


@auth_bp.route("/v1/auth/role", methods=["PUT"])
def update_role():
    access_token, error = require_access_token()
    if error:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    user, error = require_supabase_user(access_token)
    if error:
        return return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    body = request.get_json(silent=True) or {}
    role = body.get("role")
    if role not in ACTIVE_ROLES:
        return return_error("BAD_REQUEST", "Missing or invalid role data: invalid role")

    try:
        _set_active_role(str(user.id), role)
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    return jsonify({"role": role}), HTTPStatus.OK