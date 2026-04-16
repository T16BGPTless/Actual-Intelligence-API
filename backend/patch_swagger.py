import yaml

with open("../docs/swagger.yaml", "r") as f:
    text = f.read()

# For GET /v1/tokens, remove requestBody block
# It looks like:
#      requestBody:
#        required: true
#        content:
#          application/json:
#            schema:
#              type: object
#              properties:
#                accountName:
#                  type: string
#                  example: WamWarriors
#              required:
#                - accountName
get_body_str = """      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                accountName:
                  type: string
                  example: WamWarriors
              required:
                - accountName"""

text = text.replace(get_body_str, "")

# For POST /v1/tokens/buy, remove accountName from properties and required
buy_body_old = """      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                accountName:
                  type: string
                  example: Guy
                tokens:
                  type: number
                  example: 100
              required:
                - accountName
                - tokens"""
buy_body_new = """      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                tokens:
                  type: number
                  example: 100
              required:
                - tokens"""

text = text.replace(buy_body_old, buy_body_new)

# For POST /v1/tokens/redeem, remove accountName from properties and required
redeem_body_old = """      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                accountName:
                  type: string
                  example: WamWarriors
                tokens:
                  type: number
                  example: 100
              required:
                - accountName
                - tokens"""
redeem_body_new = """      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                tokens:
                  type: number
                  example: 100
              required:
                - tokens"""

text = text.replace(redeem_body_old, redeem_body_new)

with open("../docs/swagger.yaml", "w") as f:
    f.write(text)
