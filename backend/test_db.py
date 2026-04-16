from app.supabase_client import service_client, user_client
import sys
admin_client = service_client()
print(admin_client.table("chats").select("*").limit(1).execute())
res = admin_client.rpc(
            "create_chat_with_initial_request",
            {
                "p_category": "test",
                "p_request_text": "text",
                "p_tokens_to_spend": 1,
            },
        ).execute()
print(res)
