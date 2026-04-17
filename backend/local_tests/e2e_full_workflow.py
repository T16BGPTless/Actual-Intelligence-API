import requests
import sys
import uuid
import time

BASE_URL = "http://127.0.0.1:5001"

def p(msg):
    print(f"\n====================================")
    print(f"==> {msg}")
    print(f"====================================\n")

def check_status(response, expected=200):
    if response.status_code != expected:
        print(f"ERROR: Expected {expected}, got {response.status_code}")
        print(response.text)
        sys.exit(1)

def run_workflow():
    unique_id = str(uuid.uuid4())[:8]
    
    # 1. Register User 1 (Requester)
    p("1. Registering Requester (User 1)")
    req_email = f"req_{unique_id}@example.com"
    req_res = requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "Alice Requester", 
        "username": f"alice_{unique_id}", 
        "email": req_email, 
        "password": "password123"
    })
    check_status(req_res, 201)
    req_token = req_res.json().get("accessToken")
    print(f"Requester registered. Token: {req_token[:15]}...")

    # 2. Register User 2 (Responder)
    p("2. Registering Responder (User 2)")
    res_email = f"res_{unique_id}@example.com"
    res_res = requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "Bob Responder", 
        "username": f"bob_{unique_id}", 
        "email": res_email, 
        "password": "password123"
    })
    check_status(res_res, 201)
    res_token = res_res.json().get("accessToken")
    print(f"Responder registered. Token: {res_token[:15]}...")

    # 2.5 Register Malicious Users
    p("2.5 Registering Malicious Extra Users")
    mal_req_res = requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "Eve Malicious Requester", 
        "username": f"eve_req_{unique_id}", 
        "email": f"evereq_{unique_id}@example.com", 
        "password": "password123"
    })
    check_status(mal_req_res, 201)
    mal_req_token = mal_req_res.json().get("accessToken")

    mal_res_res = requests.post(f"{BASE_URL}/v1/auth/register", json={
        "name": "Eve Malicious Responder", 
        "username": f"eve_res_{unique_id}", 
        "email": f"everes_{unique_id}@example.com", 
        "password": "password123"
    })
    check_status(mal_res_res, 201)
    mal_res_token = mal_res_res.json().get("accessToken")
    print("Registered extra malicious responder and requester.")

    # 3. Requester buys tokens
    p("3. Requester buying tokens")
    buy_res = requests.post(f"{BASE_URL}/v1/tokens/buy", json={"tokens": 500}, headers={"AccessToken": req_token})
    check_status(buy_res, 200)
    
    tokens_res = requests.get(f"{BASE_URL}/v1/tokens", headers={"AccessToken": req_token})
    check_status(tokens_res, 200)
    print(f"Requester token balance: {tokens_res.json()}")

    # 4. Requester creates a Chat
    p("4. Requester creates a new chat")
    chat_res = requests.post(f"{BASE_URL}/v1/requester/chats", json={
        "requestText": f"Can someone help me write a poem? {unique_id}", 
        "category": "writing", 
        "tokensToSpend": 50
    }, headers={"AccessToken": req_token})
    check_status(chat_res, 201)
    chat_id = chat_res.json()["chatID"]
    print(f"Chat created successfully! Chat ID: {chat_id}")

    # 5. Responder browses unclaimed chats
    p("5. Responder browses unclaimed chats")
    br_res = requests.get(f"{BASE_URL}/v1/responder/chats/unclaimed", headers={"AccessToken": res_token})
    check_status(br_res, 200)
    open_chats = br_res.json()
    print(f"Found {len(open_chats)} open/unclaimed chats.")
    
    # Ensure our chat is in the list
    if not any(c.get("chatID") == chat_id for c in open_chats):
        print("ERROR: Newly created chat not found in unclaimed list!")
        sys.exit(1)

    # 6. Responder claims the chat
    p("6. Responder claims the chat")
    claim_res = requests.post(
        f"{BASE_URL}/v1/responder/chats/{chat_id}/claim", 
        headers={"AccessToken": res_token}, 
        json={"title": "Poem Writing Assistant"}
    )
    check_status(claim_res, 200)
    print("Chat successfully claimed.")

    # 6.5 Verify security constraints
    p("6.5 Verifying malicious users cannot access or tamper with claimed chat")
    
    # Malicious responder trying to claim already claimed chat
    mal_claim_res = requests.post(f"{BASE_URL}/v1/responder/chats/{chat_id}/claim", headers={"AccessToken": mal_res_token}, json={"title": "Steal job"})
    if mal_claim_res.status_code == 200:
        print("SECURITY FAILED: Malicious responder successfully claimed an already claimed chat.")
        sys.exit(1)
        
    # Malicious responder trying to view the claimed chat
    mal_view_res = requests.get(f"{BASE_URL}/v1/responder/chats/{chat_id}", headers={"AccessToken": mal_res_token})
    if mal_view_res.status_code == 200:
        print("SECURITY FAILED: Malicious responder successfully viewed someone else's claimed chat.")
        sys.exit(1)
        
    # Malicious responder trying to send a message
    mal_msg_res = requests.post(f"{BASE_URL}/v1/responder/chats/{chat_id}/messages", headers={"AccessToken": mal_res_token}, json={"message": "Hack"})
    if mal_msg_res.status_code == 201:
        print("SECURITY FAILED: Malicious responder successfully sent a message.")
        sys.exit(1)
        
    # Malicious requester trying to view the chat
    mal_req_view = requests.get(f"{BASE_URL}/v1/requester/chats/{chat_id}", headers={"AccessToken": mal_req_token})
    if mal_req_view.status_code == 200:
        print("SECURITY FAILED: Malicious requester successfully viewed someone else's chat.")
        sys.exit(1)

    # Malicious requester trying to send a message
    mal_req_msg = requests.post(f"{BASE_URL}/v1/requester/chats/{chat_id}/messages", headers={"AccessToken": mal_req_token}, json={"message": "Hack"})
    if mal_req_msg.status_code == 201:
        print("SECURITY FAILED: Malicious requester successfully sent a message as another user.")
        sys.exit(1)
        
    print("Security verifies: Malicious users are properly blocked from interfering.")

    # 7. Responder views their claimed chats
    p("7. Responder views their claimed chats")
    claimed_res = requests.get(f"{BASE_URL}/v1/responder/chats", headers={"AccessToken": res_token})
    check_status(claimed_res, 200)
    my_claimed_chats = claimed_res.json()
    print(f"Responder has {len(my_claimed_chats)} claimed chats.")
    if not any(c.get("chatID") == chat_id for c in my_claimed_chats):
        print("ERROR: Claimed chat not reflecting in responder claimed chats!")
        sys.exit(1)

    # 8. Responder sends a message (creates a solution)
    p("8. Responder sends a message")
    msg_res = requests.post(
        f"{BASE_URL}/v1/responder/chats/{chat_id}/messages", 
        headers={"AccessToken": res_token}, 
        json={"message": "Here is a nice poem about flowers..."}
    )
    check_status(msg_res, 201)
    print("Responder message sent.")

    # 9. Requester sends a reply
    p("9. Requester sends a response message")
    req_msg_res = requests.post(
        f"{BASE_URL}/v1/requester/chats/{chat_id}/messages", 
        headers={"AccessToken": req_token}, 
        json={"message": "Thanks! Could you add a stanza about the moon?", "tokensToSpend": 10}
    )
    check_status(req_msg_res, 201)
    print("Requester message 1 sent.")

    p("9.5 More back-and-forth chatter")
    requests.post(
        f"{BASE_URL}/v1/responder/chats/{chat_id}/messages", 
        headers={"AccessToken": res_token}, 
        json={"message": "Sure, here's a moon stanza: The moon glows bright, illuminating the night."}
    )
    
    requests.post(
        f"{BASE_URL}/v1/requester/chats/{chat_id}/messages", 
        headers={"AccessToken": req_token}, 
        json={"message": "Perfect! Can we also mention stars?", "tokensToSpend": 5}
    )
    
    requests.post(
        f"{BASE_URL}/v1/responder/chats/{chat_id}/messages", 
        headers={"AccessToken": res_token}, 
        json={"message": "Of course! Thousands of stars twinkle around."}
    )
    
    requests.post(
        f"{BASE_URL}/v1/requester/chats/{chat_id}/messages", 
        headers={"AccessToken": req_token}, 
        json={"message": "Awesome. Let's wrap it up.", "tokensToSpend": 2}
    )
    
    print("Simulated additional 4 messages in the chat.")

    # 10. Responder views the chat contents
    p("10. Responder views full chat history")
    res_chat_detail = requests.get(
        f"{BASE_URL}/v1/responder/chats/{chat_id}", 
        headers={"AccessToken": res_token}
    )
    check_status(res_chat_detail, 200)
    messages = res_chat_detail.json().get("messages", [])
    print(f"Chat currently has {len(messages)} messages.")
    if len(messages) < 6:
        print("ERROR: Chat message count is incorrect.")
        sys.exit(1)

    # 10.5 Simulate another user creating a separate chat while this happens
    p("10.5 Malicious Requester creating a legitimate separate chat to add chatter volume")
    mal_req_buy = requests.post(f"{BASE_URL}/v1/tokens/buy", json={"tokens": 100}, headers={"AccessToken": mal_req_token})
    check_status(mal_req_buy, 200)
    
    chat2_res = requests.post(f"{BASE_URL}/v1/requester/chats", json={
        "requestText": "Help me translate this to French.", 
        "category": "translation", 
        "tokensToSpend": 30
    }, headers={"AccessToken": mal_req_token})
    check_status(chat2_res, 201)
    chat2_id = chat2_res.json()["chatID"]
    
    # Let Malicious Responder claim the second chat
    claim2_res = requests.post(
        f"{BASE_URL}/v1/responder/chats/{chat2_id}/claim", 
        headers={"AccessToken": mal_res_token}, 
        json={"title": "French Translation"}
    )
    check_status(claim2_res, 200)
    
    requests.post(
        f"{BASE_URL}/v1/responder/chats/{chat2_id}/messages", 
        headers={"AccessToken": mal_res_token}, 
        json={"message": "Bonjour!"}
    )
    print("Secondary chat created, claimed, and messaging started successfully.")
    
    # 11. Responder closes the chat
    p("11. Responder signals closing the chat")
    close_res = requests.post(
        f"{BASE_URL}/v1/responder/chats/{chat_id}/close", 
        headers={"AccessToken": res_token}
    )
    check_status(close_res, 200)
    print("Chat closed by responder. Entering closing review state.")

    # 12. Requester reviews the chat
    p("12. Requester reviews the conversation")
    review_res = requests.post(
        f"{BASE_URL}/v1/requester/chats/{chat_id}/review", 
        headers={"AccessToken": req_token},
        json={"rating": 5, "resolved": True}
    )
    check_status(review_res, 200)
    print("Review submitted successfully!")

    # 13. Verify final chat state
    p("13. Fetching final chat state")
    final_chat = requests.get(
        f"{BASE_URL}/v1/requester/chats/{chat_id}", 
        headers={"AccessToken": req_token}
    )
    check_status(final_chat, 200)
    data = final_chat.json()
    print(f"Final Chat Status: {data.get('status')} | Claim State: {data.get('claim_state')}")
    
    if data.get("status") == "resolved" or data.get("status") == "closed":
        print("Success: Chat correctly progressed through all states.")
    
    p("ALL WORKFLOW TESTS PASSED.")

if __name__ == "__main__":
    url_arg = sys.argv[1] if len(sys.argv) > 1 else None
    if url_arg:
        BASE_URL = url_arg.rstrip("/")
        
    print(f"Running full workflow test against {BASE_URL}")
    run_workflow()