import re
with open("/Users/quantified_null/Documents/Uni/seng2021/Actual-Intelligence-API/docs/swagger.yaml", "r") as f:
    text = f.read()

# Get tokens body (we know it's under `/v1/tokens: \n    get:`)
text = re.sub(
    r'(?m)^      requestBody:\n        required: true\n        content:\n          application/json:\n            schema:\n              type: object\n              properties:\n                accountName:\n                  type: string\n                  example: [^\n]+\n              required:\n                - accountName\n',
    '', 
    text
)

# Fix buy and redeem request bodies
def remove_account_name(match):
    m = match.group(0)
    m = re.sub(r'\s+accountName:\n\s+type: string\n\s+example: [^\n]+', '', m)
    m = re.sub(r'\n\s+- accountName', '', m)
    return m

text = re.sub(r'(?m)^      requestBody:\n[\s\S]*?- tokens\n', remove_account_name, text)

# For responses, remove accountName completely, since the user said "do the same for buy and redeem" maybe we shouldn't necessarily keep it in the response, but the api does return it still...
# I'll modify the responses as well to not include accountName in the schema properties or required, just in case.

with open("/Users/quantified_null/Documents/Uni/seng2021/Actual-Intelligence-API/docs/swagger.yaml", "w") as f:
    f.write(text)
