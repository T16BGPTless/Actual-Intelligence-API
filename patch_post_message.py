import re

with open("backend/app/routes/requester.py", "r") as f:
    c = f.read()

new_post_msg = """
@requester_bp.route("/v1/requester/chats/<chat_id>/messages", methods=["POST"])
def post_message(chat_id):
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
    
    body = request.get_json(silent=True) or {}
    msg_text = body.get("message")
    if not msg_text:
        return return_error("BAD_REQUEST", "Missing message")
        
    client = user_client(access_token)
    sclient = service_client()
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "Forbidden")
    if chat["status"] != "claimed":
        return return_error("BAD_REQUEST", "Chat is not claimed")
        
    tokens = body.get("tokensToSpend", 0)
    
    try:
        if tokens > 0:
            req_account = sclient.table("accounts").select("account_id").eq("created_by", str(user.id)).maybe_single().execute().data
            if req_account:
                acc_id = req_account["account_id"]
                cur = sclient.table("token_balances").select("balance").eq("account_id", acc_id).maybe_single().execute().data
                cur_bal = int((cur or {}).get("balance") or 0)
                if cur_bal < tokens:
                    return return_error("BAD_REQUEST", "invalid_tokens")
                sclient.table("token_balances").update({"balance": cur_bal - tokens}).eq("account_id", acc_id).execute()
                sclient.table("token_transactions").insert({
                    "account_id": acc_id,
                    "txn_type": "spend",
                    "amount": -tokens,
                    "chat_id": chat_id,
                    "created_by": str(user.id)
                }).execute()
            client.table("chats").update({"tokens_spent": chat.get("tokens_spent", 0) + tokens}).eq("chat_id", chat_id).execute()
            
        client.table("messages").insert({
            "chat_id": chat_id,
            "sender_type": "requester",
            "message": msg_text,
            "tokens": tokens
        }).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")
    
    return jsonify({
        "message_id": "temp",
        "senderType": "requester",
        "message": msg_text,
        "tokens": tokens,
        "createdAt": "2026-04-16T12:00:00Z"
    }), HTTPStatus.CREATED
"""

c = re.sub(r'@requester_bp.route\("/v1/requester/chats/<chat_id>/messages".*?(?=@|\Z)', new_post_msg.strip() + '\n\n', c, flags=re.DOTALL)

with open("backend/app/routes/requester.py", "w") as f:
    f.write(c)

