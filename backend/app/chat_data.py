"""Chat and auth-related reads/writes against Supabase (RLS enforced via user JWT)."""

from __future__ import annotations
from typing import Any
from postgrest.exceptions import APIError

def api_ts(value: Any) -> str:
    if value is None:
        return ""
    s = str(value)
    if s.endswith("+00:00"):
        return s[:-6] + "Z"
    return s

def categories_from_flask_arg(values: list[str] | None, raw: str | None) -> list[str] | None:
    merged: list[str] = []
    if values:
        merged.extend(values)
    if len(merged) == 1 and "," in merged[0]:
        merged = [p.strip() for p in merged[0].split(",") if p.strip()]
    if not merged and raw:
        merged = [p.strip() for p in raw.split(",") if p.strip()]
    return merged if merged else None

def profile_map(client, user_ids: set[str]) -> dict[str, dict]:
    ids = [i for i in user_ids if i]
    if not ids:
        return {}
    rows = client.table("profiles").select("user_id,username,display_name").in_("user_id", ids).execute().data or []
    return {str(r["user_id"]): r for r in rows}

def chat_summary_dict(client, chat: dict) -> dict:
    return {
        "chatID": chat["chat_id"],
        "title": chat.get("title"),
        "originalRequest": chat.get("original_request") or "",
        "category": chat.get("category") or "",
        "status": chat["status"],
        "tokens": int(chat.get("tokens_spent") or 0),
        "createdAt": api_ts(chat.get("created_at")),
    }

def message_dict(row: dict) -> dict:
    return {
        "senderType": row["sender_type"],
        "message": row["message"],
        "tokens": row.get("tokens", 0),
        "createdAt": api_ts(row.get("created_at")),
    }

def build_chat_detail(client, chat: dict) -> dict:
    cid = chat["chat_id"]
    uid_set = {str(chat["requester_id"]), str(chat["responder_id"]) if chat.get("responder_id") else ""}
    uid_set.discard("")
    pmap = profile_map(client, uid_set)
    rq = str(chat["requester_id"])
    rr = str(chat["responder_id"]) if chat.get("responder_id") else None
    req_username = pmap.get(rq, {}).get("username") or ""
    res_username = pmap.get(rr, {}).get("username") if rr else None

    msgs = client.table("messages").select("message_id,sender_type,message,tokens,created_at").eq("chat_id", cid).order("created_at", desc=False).execute().data or []
    
    return {
        "chatID": cid,
        "title": chat.get("title"),
        "originalRequest": chat.get("original_request") or "",
        "category": chat.get("category") or "",
        "requesterUsername": req_username,
        "responderUsername": res_username,
        "status": chat["status"],
        "tokensSpent": int(chat.get("tokens_spent") or 0),
        "createdAt": api_ts(chat.get("created_at")),
        "messages": [message_dict(m) for m in msgs],
    }

def get_chat_or_none(client, chat_id: str) -> dict | None:
    res = client.table("chats").select("*").eq("chat_id", chat_id).maybe_single().execute()
    if not res: return None
    if isinstance(res, dict): return res
    if hasattr(res, "data"): return res.data
    return None

def create_chat_with_initial_request(client, body: dict) -> tuple[dict | None, str | None]:
    tokens_raw = body.get("tokensToSpend")
    if tokens_raw is None:
        return None, "invalid_tokens"
    try:
        tokens = int(tokens_raw)
    except (TypeError, ValueError):
        return None, "invalid_tokens"
    if tokens <= 0:
        return None, "invalid_tokens"

    try:
        res = client.rpc(
            "create_chat_with_initial_request",
            {
                "p_category": (body.get("category") or "") if isinstance(body.get("category"), str) else "",
                "p_request_text": body["requestText"],
                "p_tokens_to_spend": tokens,
            },
        ).execute()
    except APIError as e:
        import traceback; traceback.print_exc()
        print(e)
        return None, "rpc_failed"

    payload = res.data
    if isinstance(payload, list):
        payload = payload[0] if payload else None
    if not payload or not payload.get("ok"):
        return None, "rpc_failed"
    
    # Optional update title
    if body.get("title"):
        try:
            client.table("chats").update({"title": body["title"]}).eq("chat_id", payload["chat_id"]).execute()
        except:
            pass
            
    return payload, None
