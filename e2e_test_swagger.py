import requests
import sys

BASE_URL = "http://127.0.0.1:5003"

def p(msg):
    print(f"==> {msg}")

# 1. Register requester
p("Register requester")
req_res = requests.post(f"{BASE_URL}/v1/auth/register", json={
    "name": "Req", "username": "requester", "email": "req@example.com", "password": "password"
})
if req_res.status_code != 201:
    print(req_res.text)
req_token = req_res.json()["accessToken"]

# 2. Register responder
p("Register responder")
res_res = requests.post(f"{BASE_URL}/v1/auth/register", json={
    "name": "Res", "username": "responder", "email": "res@example.com", "password": "password"
})
if res_res.status_code != 201:
    print(res_res.text)
res_token = res_res.json()["accessToken"]

# 3. Create a chat
p("Create Chat")
chat_res = requests.post(f"{BASE_URL}/v1/requester/chats", json={
    "requestText": "test req", "category": "writing", "tokensToSpend": 10
}, headers={"AccessToken": req_token})
if chat_res.status_code != 201:
    print("FAILED", chat_res.status_code, chat_res.text)
cid = chat_res.json()["chatID"]

# 4. Browse chats as responder
p("Browse Chats")
br_res = requests.get(f"{BASE_URL}/v1/responder/chats", headers={"AccessToken": res_token})
print(br_res.json())

# 5. Browse chats as requester
p("Browse as requester")
brr_res = requests.get(f"{BASE_URL}/v1/requester/chats", headers={"AccessToken": req_token})
print(brr_res.json())

