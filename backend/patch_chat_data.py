import re

with open("app/chat_data.py", "r") as f:
    c = f.read()

c = c.replace('except APIError:', 'except APIError as e:\n        return None, str(e.message)')
c = c.replace('if not payload or not payload.get("ok"):', 'if not payload or not payload.get("ok"):\n        return None, "payload_nok"')

with open("app/chat_data.py", "w") as f:
    f.write(c)

