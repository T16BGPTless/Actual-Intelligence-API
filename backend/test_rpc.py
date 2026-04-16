from app.supabase_client import service_client
client = service_client()
try:
    res = client.rpc("create_chat_with_initial_request", {
        "p_category": "test",
        "p_request_text": "text",
        "p_tokens_to_spend": 1,
    }).execute()
    print(res)
except Exception as e:
    import traceback
    traceback.print_exc()
