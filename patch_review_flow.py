import re

with open("backend/app/routes/requester.py", "r") as f:
    c = f.read()

# We need to transfer tokens in review_chat.
new_review = """
@requester_bp.route("/v1/requester/chats/<chat_id>/review", methods=["POST"])
def review_chat(chat_id):
    access_token, error = require_access_token()
    if error: return error
    user, error = require_supabase_user(access_token)
    if error: return error
        
    body = request.get_json(silent=True) or {}
    rating = body.get("rating")
    
    client = user_client(access_token)
    sclient = service_client()
    chat = get_chat_or_none(client, chat_id)
    if not chat:
        return return_error("NOT_FOUND", "Not Found")
    if str(chat["requester_id"]) != str(user.id):
        return return_error("FORBIDDEN", "Forbidden")
    if chat["status"] != "closing":
        return return_error("BAD_REQUEST", "Chat is not closing")
        
    upd = {"status": "closed", "resolved": body.get("resolved", True)}
    if rating:
        upd["rating"] = rating
        
    try:
        # Payout tokens to responder
        responder_id = chat.get("responder_id")
        tokens_spent = int(chat.get("tokens_spent") or 0)
        
        if responder_id and tokens_spent > 0:
            res_account = sclient.table("accounts").select("account_id").eq("created_by", responder_id).maybe_single().execute().data
            if res_account:
                acc_id = res_account["account_id"]
                # get current balance
                cur = sclient.table("token_balances").select("balance").eq("account_id", acc_id).maybe_single().execute().data
                cur_bal = int((cur or {}).get("balance") or 0)
                
                sclient.table("token_balances").update({"balance": cur_bal + tokens_spent}).eq("account_id", acc_id).execute()
                sclient.table("token_transactions").insert({
                    "account_id": acc_id,
                    "txn_type": "adjustment",
                    "amount": tokens_spent,
                    "chat_id": chat_id,
                    "created_by": str(user.id)
                }).execute()

        client.table("chats").update(upd).eq("chat_id", chat_id).execute()
    except APIError:
        return return_error("INTERNAL_SERVER_ERROR")
    
    return jsonify({"message": "Chat successfully closed."}), HTTPStatus.OK
"""

c = re.sub(r'@requester_bp.route\("/v1/requester/chats/<chat_id>/review".*?(?=@|\Z)', new_review.strip() + '\n\n', c, flags=re.DOTALL)

with open("backend/app/routes/requester.py", "w") as f:
    f.write(c)

