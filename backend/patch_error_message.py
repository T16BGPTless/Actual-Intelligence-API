with open("../docs/swagger.yaml", "r") as f:
    c = f.read()

c = c.replace('message: accountName cannot be found', 'message: account cannot be found')

with open("../docs/swagger.yaml", "w") as f:
    f.write(c)
