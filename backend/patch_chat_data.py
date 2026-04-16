import re

with open("app/chat_data.py", "r") as f:
    text = f.read()

# Make sure we don't output messageID and output tokens.
text = re.sub(r'def message_dict\(row: dict\) -> dict:.*?return \{.*?\}', r'''def message_dict(row: dict) -> dict:
    return {
        "senderType": row["sender_type"],
        "message": row["message"],
        "tokens": row.get("tokens", 0),
        "createdAt": api_ts(row.get("created_at")),
    }''', text, flags=re.DOTALL)

# Refactor build_chat_detail to merge messages and requests.
new_build_chat_detail = r'''def build_chat_detail(client, chat: dict) -> dict:
    cid = chat["chat_id"]
    uid_set = {
        str(chat["requester_id"]),
        str(chat["responder_id"]) if chat.get("responder_id") else "",
    }
    uid_set.discard("")
    pmap = profile_map(client, uid_set)
    rq = str(chat["requester_id"])
    rr = str(chat["responder_id"]) if chat.get("responder_id") else None
    req_row = pmap.get(rq, {})
    res_row = pmap.get(rr, {}) if rr else {}
    req_username = req_row.get("username") or ""
    res_username = res_row.get("username") if rr else None

    msgs = (
        client.table("messages")
        .select("message_id,sender_type,message,created_at")
        .eq("chat_id", cid)
        .order("created_at", desc=False)
        .execute()
        .data
        or []
    )
    reqs = (
        client.table("requests")
        .select("request_id,request_text,status,tokens_to_spend,created_at")
        .eq("chat_id", cid)
        .order("created_at", desc=False)
        .execute()
        .data
        or []
    )

    combined_messages = []
    
    # Map DB messages
    for m in msgs:
        combined_messages.append({
            "senderType": m["sender_type"],
            "message": m["message"],
            "tokens": 0,
            "createdAt": api_ts(m.get("created_at")),
            "_ts": m.get("created_at")
        })
        
    # Map DB requests (except the first one which goes to originalRequest), 
    # Wait, the swagger says "add a new request to an existing chat... adding a new request to messages should be handled within the main messages post request". 
    # Actually if the user created a request, should it appear as a message? The swagger says "all messages and requests are the same thing except the initial request, which should be in the main body".
    
    original_request = ""
    tokens_spent = 0
    
    if reqs:
        # First request is the original request
        original_request = reqs[0]["request_text"]
        tokens_spent += int(reqs[0]["tokens_to_spend"])
        
        # Subsequent requests are treated as messages
        for r in reqs[1:]:
            tokens_spent += int(r["tokens_to_spend"])
            combined_messages.append({
                "senderType": "requester",
                "message": r["request_text"],
                "tokens": int(r["tokens_to_spend"]),
                "createdAt": api_ts(r.get("created_at")),
                "_ts": r.get("created_at")
            })
            
    # Sort chronologically
    combined_messages.sort(key=lambda x: x["_ts"] or "")
    for m in combined_messages:
        del m["_ts"]

    return {
        "chatID": cid,
        "title": chat.get("title"),
        "originalRequest": original_request,
        "category": chat.get("category") or "",
        "requesterUsername": req_username,
        "responderUsername": res_username,
        "status": chat["status"],
        "tokensSpent": tokens_spent,
        "createdAt": api_ts(chat.get("created_at")),
        "messages": combined_messages,
    }'''

text = re.sub(r'def build_chat_detail\(client, chat: dict\) -> dict:.*?return \{.*?\}', new_build_chat_detail, text, flags=re.DOTALL)

with open("app/chat_data.py", "w") as f:
    f.write(text)
