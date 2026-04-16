import re

with open("app/routes/tokens.py", "r") as f:
    code = f.read()

# Instead of fetching by account_name from body, fetch by created_by from user
# We need to change _account_for_name or make a new one: _account_for_user

old_code = """
@tokens_bp.route("/v1/tokens", methods=["GET"])
def get_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    account_name = _require_account_name(body)
    if not account_name:
        return return_error(
            "BAD_REQUEST", "Missing or invalid data: accountName is required"
        )

    client = service_client()
    try:
        account = _account_for_name(client, account_name)
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    if not account:
        return return_error("NOT_FOUND", "accountName cannot be found")
    if str(account.get("created_by")) != str(user.id):
        return return_error("FORBIDDEN")
"""

new_code = """
def _account_for_user(client, user_id: str):
    return _execute_data(
        client.table("accounts")
        .select("account_id,account_name,created_by")
        .eq("created_by", user_id)
        .order("created_at")
        .limit(1)
        .maybe_single()
    )

@tokens_bp.route("/v1/tokens", methods=["GET"])
def get_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    client = service_client()
    try:
        account = _account_for_user(client, str(user.id))
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    if not account:
        return return_error("NOT_FOUND", "User account cannot be found")
"""

code = code.replace(old_code.strip(), new_code.strip())

with open("app/routes/tokens.py", "w") as f:
    f.write(code)
