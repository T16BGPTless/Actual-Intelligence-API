"""Helper functions for the routes."""

from http import HTTPStatus
from flask import jsonify, request, Response

def return_error(error: str, custom_message: str = None) -> tuple[Response, int]:
    """Return an error response formatted to the OpenAPI Error schema."""
    error_map = {
        "BAD_REQUEST": (HTTPStatus.BAD_REQUEST, "Missing or invalid data."),
        "UNAUTHORIZED": (HTTPStatus.UNAUTHORIZED, "Missing or invalid bearer token"),
        "INTERNAL_SERVER_ERROR": (
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "An internal server error occurred. If this persists contact us at contact@gptless.au."
        ),
        "UNKNOWN": (HTTPStatus.INTERNAL_SERVER_ERROR, "An unknown error occurred"),
    }
    
    status, default_message = error_map.get(error, error_map["UNKNOWN"])
    
    return jsonify({
        "error": error,
        "message": custom_message or default_message
    }), status


def require_access_token() -> tuple[str | None, tuple[Response, int] | None]:
    """Validate that the AccessToken header is present."""
    access_token = request.headers.get("AccessToken")

    if not access_token:
        return None, return_error("UNAUTHORIZED", "Missing or invalid bearer token")

    return access_token, None