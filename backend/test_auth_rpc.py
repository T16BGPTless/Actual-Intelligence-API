from app.supabase_client import service_client, create_client, supabase_url, supabase_anon_key
client = create_client(supabase_url(), supabase_anon_key())
try:
    res = client.auth.sign_up({"email": "testrpc@example.com", "password": "password123"})
    print("sign up ok", getattr(res, 'user', 'no user'))
except Exception as e:
    print(e)
    res = client.auth.sign_in_with_password({"email": "testrpc@example.com", "password": "password123"})

token = client.auth.get_session().access_token
# print(token)
from app.chat_data import create_chat_with_initial_request
from app.routes.requester import user_client

uclient = user_client(token)
payload, err = create_chat_with_initial_request(uclient, {
    "category": "writing",
    "requestText": "hello world",
    "tokensToSpend": 1
})
print("PAYLOAD:", payload)
print("ERR:", err)
