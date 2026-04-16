import re

with open("app/routes/tokens.py", "r") as f:
    code = f.read()

# Remove _require_account_name and _account_for_name as they are no longer needed
code = re.sub(r'def _require_account_name.*?return account_name\.strip\(\)\n', '', code, flags=re.DOTALL)
code = re.sub(r'def _account_for_name.*?.maybe_single\(\)\n    \)\n', '', code, flags=re.DOTALL)

# Patch buy_tokens
old_buy = """
@tokens_bp.route("/v1/tokens/buy", methods=["POST"])
def buy_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    account_name = _require_account_name(body)
    tokens = _require_positive_tokens(body)
    if not account_name or tokens is None:
        return return_error("BAD_REQUEST", "Missing or invalid data.")

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

new_buy = """
@tokens_bp.route("/v1/tokens/buy", methods=["POST"])
def buy_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    tokens = _require_positive_tokens(body)
    if tokens is None:
        return return_error("BAD_REQUEST", "Missing or invalid data: tokens required.")

    client = service_client()
    try:
        account = _account_for_user(client, str(user.id))
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    if not account:
        return return_error("NOT_FOUND", "User account cannot be found")
"""
code = code.replace(old_buy.strip(), new_buy.strip())

# Patch redeem_tokens
old_redeem = """
@tokens_bp.route("/v1/tokens/redeem", methods=["POST"])
def redeem_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    account_name = _require_account_name(body)
    tokens = _require_positive_tokens(body)
    if not account_name or tokens is None:
        return return_error("BAD_REQUEST", "Missing or invalid data.")

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

new_redeem = """
@tokens_bp.route("/v1/tokens/redeem", methods=["POST"])
def redeem_tokens():
    access_token, error = require_access_token()
    if error:
        return error
    user, error = require_supabase_user(access_token)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    tokens = _require_positive_tokens(body)
    if tokens is None:
        return return_error("BAD_REQUEST", "Missing or invalid data: tokens required.")

    client = service_client()
    try:
        account = _account_for_user(client, str(user.id))
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")

    if not account:
        return return_error("NOT_FOUND", "User account cannot be found")
"""
code = code.replace(old_redeem.strip(), new_redeem.strip())

with open("app/routes/tokens.py", "w") as f:
    f.write(code)

