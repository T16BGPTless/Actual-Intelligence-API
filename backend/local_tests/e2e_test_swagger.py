import requests
import sys
import uuid

BASE_URL = "http://127.0.0.1:5002"  
PASS = True

def check_success(res, exp_status):
    global PASS
    if res.status_code != exp_status:
        print(f"[{res.request.method} {res.request.url}] FAIL: Exp status {exp_status} got {res.status_code}. Body: {res.text}")
        PASS = False
        return False
    # Passed!
    print(f"[{res.request.method} {res.request.url}] PASS: SUCCESS {exp_status}")
    return True

def check_res(res, exp_status, exp_error):
    global PASS
    if res.status_code != exp_status:
        print(f"[{res.request.method} {res.request.url}] FAIL: Exp status {exp_status} got {res.status_code}. Body: {res.text}")
        PASS = False
        return False
    try:
        data = res.json()
        if data.get("error") != exp_error:
            print(f"[{res.request.method} {res.request.url}] FAIL: Exp error {exp_error} got {data.get('error')}. Body: {res.text}")
            PASS = False
            return False
        if "message" not in data:
            print(f"[{res.request.method} {res.request.url}] FAIL: No 'message' in response. Body: {res.text}")
            PASS = False
            return False
        # Passed!
        print(f"[{res.request.method} {res.request.url}] PASS: {exp_error}")
        return True
    except Exception as e:
        print(f"[{res.request.method} {res.request.url}] FAIL: Error parsing json {e}. Body: {res.text}")
        PASS = False
        return False

def p(msg):
    print(f"\n==> {msg}")

# Setup users
run_id = uuid.uuid4().hex[:6]
req_user = {"name":"Req", "username":f"req_{run_id}", "email":f"req_{run_id}@example.com", "password":"password"}
res_user = {"name":"Res", "username":f"res_{run_id}", "email":f"res_{run_id}@example.com", "password":"password"}

tok_req = requests.post(f"{BASE_URL}/v1/auth/register", json=req_user).json()["accessToken"]
import os
import urllib.request
import json

tok_res = requests.post(f"{BASE_URL}/v1/auth/register", json=res_user).json()["accessToken"]
print("Responder token:", tok_res)

bad_id = uuid.uuid4()

p("Testing Auth Errors")
# POST /v1/auth/register
check_res(requests.post(f"{BASE_URL}/v1/auth/register", json={}), 400, "BAD_REQUEST")
check_res(requests.post(f"{BASE_URL}/v1/auth/register", json=req_user), 409, "CONFLICT")

# POST /v1/auth/login
check_res(requests.post(f"{BASE_URL}/v1/auth/login", json={}), 400, "BAD_REQUEST")
check_res(requests.post(f"{BASE_URL}/v1/auth/login", json={"email": "notfound@example.com", "password": "wrong"}), 401, "UNAUTHORIZED")

# POST /v1/auth/logout
check_res(requests.post(f"{BASE_URL}/v1/auth/logout", headers={}), 401, "UNAUTHORIZED")
check_res(requests.post(f"{BASE_URL}/v1/auth/logout", headers={"AccessToken": "invalid"}), 401, "UNAUTHORIZED")

# GET /v1/auth/me
check_res(requests.get(f"{BASE_URL}/v1/auth/me", headers={}), 401, "UNAUTHORIZED")


p("Testing Requester Errors")

# POST /v1/requester/chats
check_res(requests.post(f"{BASE_URL}/v1/requester/chats", json={"requestText":"hi"}), 401, "UNAUTHORIZED")
check_res(requests.post(f"{BASE_URL}/v1/requester/chats", json={}, headers={"AccessToken": tok_req}), 400, "BAD_REQUEST")

# Create a real chat
requests.post(f"{BASE_URL}/v1/tokens/buy", json={"tokens": 100}, headers={"AccessToken": tok_req})
cr1_res = requests.post(f"{BASE_URL}/v1/requester/chats", json={
    "requestText": f"Can someone help me write a poem?", 
    "category": "writing", 
    "tokensToSpend": 50
}, headers={"AccessToken": tok_req})
print(cr1_res.json())
cid = cr1_res.json()["chatID"]

# GET /v1/requester/chats
check_res(requests.get(f"{BASE_URL}/v1/requester/chats", headers={}), 401, "UNAUTHORIZED")

# GET /v1/requester/chats/{chatID}
check_res(requests.get(f"{BASE_URL}/v1/requester/chats/{cid}", headers={}), 401, "UNAUTHORIZED")
check_res(requests.get(f"{BASE_URL}/v1/requester/chats/{cid}", headers={"AccessToken": tok_res}), 403, "FORBIDDEN")
check_res(requests.get(f"{BASE_URL}/v1/requester/chats/{bad_id}", headers={"AccessToken": tok_req}), 404, "NOT_FOUND")

# POST /v1/requester/chats/{chatID}/messages
check_res(requests.post(f"{BASE_URL}/v1/requester/chats/{cid}/messages", json={}), 401, "UNAUTHORIZED")
check_res(requests.post(f"{BASE_URL}/v1/requester/chats/{cid}/messages", json={}, headers={"AccessToken": tok_req}), 400, "BAD_REQUEST")
check_res(requests.post(f"{BASE_URL}/v1/requester/chats/{cid}/messages", json={"message": "hi"}, headers={"AccessToken": tok_res}), 403, "FORBIDDEN")
check_res(requests.post(f"{BASE_URL}/v1/requester/chats/{bad_id}/messages", json={"message": "hi"}, headers={"AccessToken": tok_req}), 404, "NOT_FOUND")

# POST /v1/requester/chats/{chatID}/review
check_res(requests.post(f"{BASE_URL}/v1/requester/chats/{cid}/review", json={"resolved": True, "rating": 5}), 401, "UNAUTHORIZED")
check_res(requests.post(f"{BASE_URL}/v1/requester/chats/{cid}/review", json={"resolved": True, "rating": 5}, headers={"AccessToken": tok_res}), 403, "FORBIDDEN")
check_res(requests.post(f"{BASE_URL}/v1/requester/chats/{bad_id}/review", json={"resolved": True, "rating": 5}, headers={"AccessToken": tok_req}), 404, "NOT_FOUND")


p("Testing Responder Errors")

# GET /v1/responder/chats
check_res(requests.get(f"{BASE_URL}/v1/responder/chats", headers={}), 401, "UNAUTHORIZED")

# GET /v1/responder/chats/unclaimed
check_res(requests.get(f"{BASE_URL}/v1/responder/chats/unclaimed", headers={}), 401, "UNAUTHORIZED")

# GET /v1/responder/chats/{chatID}
check_res(requests.get(f"{BASE_URL}/v1/responder/chats/{cid}", headers={}), 401, "UNAUTHORIZED")
check_res(requests.get(f"{BASE_URL}/v1/responder/chats/{bad_id}", headers={"AccessToken": tok_res}), 404, "NOT_FOUND")

# POST /v1/responder/chats/{chatID}/claim
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/claim", json={"title": "claim"}), 401, "UNAUTHORIZED")
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/claim", json={}, headers={"AccessToken": tok_res}), 400, "BAD_REQUEST")

check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{bad_id}/claim", json={"title": "claim"}, headers={"AccessToken": tok_res}), 404, "NOT_FOUND")

# Let responder claim it successfully so we can test conflict
cl_res = requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/claim", json={"title": "Claimed"}, headers={"AccessToken": tok_res})
if cl_res.status_code == 200:
    # Double claim -> 409
    tok_res2 = requests.post(f"{BASE_URL}/v1/auth/register", json={"name":"Res2", "username":f"res2_{run_id}", "email":f"res2_{run_id}@example.com", "password":"password"}).json()["accessToken"]
    check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/claim", json={"title": "Claimed"}, headers={"AccessToken": tok_res2}), 409, "CONFLICT")
else:
    print(f"Failed to setup claim for 409 conflict test: {cl_res.text}")

# POST /v1/responder/chats/{chatID}/messages
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/messages", json={"message": "reshi"}), 401, "UNAUTHORIZED")
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/messages", json={}, headers={"AccessToken": tok_res}), 400, "BAD_REQUEST")
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/messages", json={"message": "reshi"}, headers={"AccessToken": tok_req}), 403, "FORBIDDEN")
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{bad_id}/messages", json={"message": "reshi"}, headers={"AccessToken": tok_res}), 404, "NOT_FOUND")

# POST /v1/responder/chats/{chatID}/close
# Wait, need to send responseText inside empty json? No, close description says:
# "400 Bad Request... Missing or invalid fulfillment data: missing field: responseText" Actually let's check swagger, oh wait it doesn't have requestBody in the yaml I cat'd, wait yes it does: "400 Bad Request - Missing or invalid fulfillment data... responseText" 
# Oh, my grep maybe missed the RequestBody for close or it was implicit. I'll test 400 BAD_REQUEST.
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/close", json={}), 401, "UNAUTHORIZED")
# Not the responder -> 403
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/close", json={"responseText": "done"}, headers={"AccessToken": tok_req}), 403, "FORBIDDEN")
check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{bad_id}/close", json={"responseText": "done"}, headers={"AccessToken": tok_res}), 404, "NOT_FOUND")

check_res(requests.post(f"{BASE_URL}/v1/responder/chats/{cid}/close", json={}, headers={"AccessToken": tok_res}), 400, "BAD_REQUEST")


p("Testing Tokens Errors")
check_res(requests.get(f"{BASE_URL}/v1/tokens", headers={}), 401, "UNAUTHORIZED")


p("Testing Success Paths")
test_u = {"name":"TestU", "username":f"tu_{run_id}", "email":f"tu_{run_id}@example.com", "password":"password"}
check_success(requests.post(f"{BASE_URL}/v1/auth/register", json=test_u), 201)
check_success(requests.post(f"{BASE_URL}/v1/auth/login", json={"email": req_user["email"], "password": req_user["password"]}), 200)

check_success(requests.get(f"{BASE_URL}/v1/auth/me", headers={"AccessToken": tok_req}), 200)

# Create a fresh chat for success path to avoid conflicts with previous error tests
requests.post(f"{BASE_URL}/v1/tokens/buy", json={"tokens": 100}, headers={"AccessToken": tok_req})
cr2_res = requests.post(f"{BASE_URL}/v1/requester/chats", json={
    "requestText": "This is a clean chat for success test.", 
    "category": "writing", 
    "tokensToSpend": 50
}, headers={"AccessToken": tok_req})
cid2 = cr2_res.json()["chatID"]

check_success(requests.get(f"{BASE_URL}/v1/requester/chats", headers={"AccessToken": tok_req}), 200)
check_success(requests.get(f"{BASE_URL}/v1/requester/chats/{cid2}", headers={"AccessToken": tok_req}), 200)
# claim chat before sending message
check_success(requests.post(f"{BASE_URL}/v1/responder/chats/{cid2}/claim", json={"title": "Claimed"}, headers={"AccessToken": tok_res}), 200)
check_success(requests.post(f"{BASE_URL}/v1/requester/chats/{cid2}/messages", json={"message": "from_req"}, headers={"AccessToken": tok_req}), 201)

check_success(requests.get(f"{BASE_URL}/v1/responder/chats/unclaimed", headers={"AccessToken": tok_res}), 200)
check_success(requests.get(f"{BASE_URL}/v1/responder/chats", headers={"AccessToken": tok_res}), 200)
check_success(requests.get(f"{BASE_URL}/v1/responder/chats/{cid2}", headers={"AccessToken": tok_res}), 200)
check_success(requests.post(f"{BASE_URL}/v1/responder/chats/{cid2}/messages", json={"message": "from_res"}, headers={"AccessToken": tok_res}), 201)

check_success(requests.get(f"{BASE_URL}/v1/tokens", headers={"AccessToken": tok_req}), 200)

check_success(requests.post(f"{BASE_URL}/v1/responder/chats/{cid2}/close", json={"responseText": "done"}, headers={"AccessToken": tok_res}), 200)
check_success(requests.post(f"{BASE_URL}/v1/requester/chats/{cid2}/review", json={"resolved": True, "rating": 5}, headers={"AccessToken": tok_req}), 200)

check_success(requests.post(f"{BASE_URL}/v1/auth/logout", headers={"AccessToken": tok_req}), 200)

if PASS:
    print("\nALL SWAGGER TESTS PASSED!")
    sys.exit(0)
else:
    print("\nSOME ERRORS FAILED.")
    sys.exit(1)
