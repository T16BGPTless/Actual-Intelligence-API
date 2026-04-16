import re

with open("app/chat_data.py", "r") as f:
    text = f.read()

new_chat_summary_dict = r'''def chat_summary_dict(client, chat: dict, tokens: int) -> dict:
    requests = (
        client.table("requests")
        .select("request_text")
        .eq("chat_id", chat["chat_id"])
        .order("created_at", desc=False)
        .limit(1)
        .execute()
        .data
        or []
    )
    original_request = requests[0]["request_text"] if requests else ""
    return {
        "chatID": chat["chat_id"],
        "title": chat.get("title"),
        "originalRequest": original_request,
        "category": chat.get("category") or "",
        "status": chat["status"],
        "tokens": tokens,
        "createdAt": api_ts(chat.get("created_at")),
    }'''

text = re.sub(r'def chat_summary_dict\(chat: dict, tokens: int\) -> dict:.*?return \{.*?\}', new_chat_summary_dict, text, flags=re.DOTALL)

with open("app/chat_data.py", "w") as f:
    f.write(text)
