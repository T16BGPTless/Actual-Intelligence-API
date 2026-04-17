import requests
import sys

BASE_URL = "http://127.0.0.1:5003"

def p(msg):
    print(f"==> {msg}")

# 1. Register requester
p("Register requester")
req_res = requests.post(f"{BASE_URL}/v1/auth/register", json={
    "name": "Req", "username": "req" + str(id(BASE_URL)), "email": "reqtest@example.com", "password": "password"
})
req_token = req_res.json().get("accessToken")
if not req_token:
    req_token = requests.post(f"{BASE_URL}/v1/auth/login", json={"email": "reqtest@example.com", "password": "password"}).json()["accessToken"]

# 2. Add tokens to requester
res = requests.post(f"{BASE_URL}/v1/tokens/buy", json={"tokens": 100}, headers={"AccessToken": req_token})
print("Req tokens:", requests.get(f"{BASE_URL}/v1/tokens", headers={"AccessToken": req_token}).json())

# 3. Create chat
p("Create Chat")
chat_res = requests.post(f"{BASE_URL}/v1/requester/chats", json={
    "requestText": "test req", "category": "writing", "tokensToSpend": 10
}, headers={"AccessToken": req_token})
cid = chat_res.json()["chatID"]
print("Created chat", cid)
print("Req tokens after spend:", requests.get(f"{BASE_URL}/v1/tokens", headers={"AccessToken": req_token}).json())

# 4. Responder workflow
p("Register responder")
res_res = requests.post(f"{BASE_URL}/v1/auth/register", json={
    "name": "Res", "username": "res" + str(id(BASE_URL)), "email": "restest@example.com", "password": "password"
})
res_token = res_res.json().get("accessToken")
if not res_token:
    res_token = requests.post(f"{BASE_URL}/v1/auth/login", json={"email": "restest@example.com", "password": "password"}).json()["accessToken"]

p("Browse Chats")
br_res = requests.get(f"{BASE_URL}/v1/responder/chats", headers={"AccessToken": res_token})
print("Open chats:", [c["chatID"] for c in br_res.json()])

p("Claim Chat")
print(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/claim", headers={"AccessToken": res_token}, json={"title": "Mytitle"}).json())

p("Responder msg")
print(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/messages", headers={"AccessToken": res_token}, json={"message": "res"}).json())

p("Responder close")
print(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/close", headers={"AccessToken": res_token}).json())

# 5. Requester reviews
p("Requester review")
print(requests.post(f"{BASE_URL}/v1/requester/chats/{cid}/review", headers={"AccessToken": req_token}, json={"rating": 5}).json())

# 6. Responder tokens
p("Responder tokens")
print(requests.get(f"{BASE_URL}/v1/tokens", headers={"AccessToken": res_token}).json())

