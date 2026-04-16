import re

with open("backend/app/routes/tokens.py", "r") as f:
    c = f.read()

c = c.replace('{"accountName": account["account_name"], "tokenBalance": balance}', '{"tokenBalance": balance}')
c = re.sub(r'[ \t]*"accountName": account\["account_name"\],\n*', '', c)

with open("backend/app/routes/tokens.py", "w") as f:
    f.write(c)

with open("backend/tests/test_tokens_routes.py", "r") as f:
    c = f.read()

c = re.sub(r'"accountName": "Main",\s*', '', c)

with open("backend/tests/test_tokens_routes.py", "w") as f:
    f.write(c)

with open("docs/swagger.yaml", "r") as f:
    c = f.read()

c = re.sub(r'[ \t]*accountName:\n[ \t]*type: string\n[ \t]*example: [^\n]+\n', '\n', c)

with open("docs/swagger.yaml", "w") as f:
    f.write(c)

print("Patched files successfully.")
