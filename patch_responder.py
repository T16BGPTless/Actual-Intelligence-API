with open("backend/app/routes/responder.py", "r") as f:
    c = f.read()

c = c.replace('.eq("status", "open")', '.eq("status", "open").neq("requester_id", str(user.id))')
c = c.replace('.eq("responder_id", str(user.id))', '.eq("responder_id", str(user.id)).neq("requester_id", str(user.id))')

with open("backend/app/routes/responder.py", "w") as f:
    f.write(c)

