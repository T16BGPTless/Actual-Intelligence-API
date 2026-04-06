"""Helper functions for the routes."""

from http import HTTPStatus
from flask import jsonify, request, Response
from supabase_auth.errors import AuthApiError

from app.supabase_client import anon_client


def return_error(error: str, custom_message: str = None) -> tuple[Response, int]:
    """Return an error response formatted to the OpenAPI Error schema."""
    error_map = {
        "BAD_REQUEST": (HTTPStatus.BAD_REQUEST, "Missing or invalid data."),
        "UNAUTHORIZED": (
            HTTPStatus.UNAUTHORIZED,
            "The API token is missing or invalid. If you do not have an API token "
            "register for one through the form on our website",
        ),
        "FORBIDDEN": (HTTPStatus.FORBIDDEN, "You do not have access to this content"),
        "NOT_FOUND": (HTTPStatus.NOT_FOUND, "The requested resource was not found"),
        "CONFLICT": (
            HTTPStatus.CONFLICT,
            "A conflict occurred with the current state of the resource",
        ),
        "INTERNAL_SERVER_ERROR": (
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "An internal server error occurred. If this persists contact us at contact@gptless.au.",
        ),
    }

    status, default_message = error_map.get(
        error, (HTTPStatus.INTERNAL_SERVER_ERROR, "Unknown error")
    )

    return jsonify(
        {"error": error, "message": custom_message or default_message}
    ), status


def require_access_token() -> tuple[str | None, tuple[Response, int] | None]:
    """Validate that the Authorization header is present and starts with Bearer."""
    auth_header = request.headers.get("Authorization")

    # Check if header exists and follows "Bearer <token>" format
    if not auth_header or not auth_header.startswith("Bearer "):
        return None, return_error("UNAUTHORIZED")

    access_token = auth_header.split(" ", 1)[1]

    return access_token, None


def require_supabase_user(
    access_token: str,
) -> tuple[object | None, tuple[Response, int] | None]:
    """Validate JWT with GoTrue and return the Supabase user model."""
    try:
        res = anon_client().auth.get_user(access_token)
    except AuthApiError:
        return None, return_error("UNAUTHORIZED")

    if not res or not res.user:
        return None, return_error("UNAUTHORIZED")

    return res.user, None
