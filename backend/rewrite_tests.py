import re

with open("tests/test_tokens_routes.py", "r") as f:
    text = f.read()

# Replace client.get("/v1/tokens", json={"accountName": "Main"}) with client.get("/v1/tokens")
# Replace client.get("/v1/tokens", json={"accountName": "Missing"}) with client.get("/v1/tokens")
text = re.sub(r'client\.get\("/v1/tokens",\s*json=\{.*?\}\)', 'client.get("/v1/tokens")', text)

with open("tests/test_tokens_routes.py", "w") as f:
    f.write(text)
