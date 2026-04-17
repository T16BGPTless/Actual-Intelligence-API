import sys
sys.path.append('.')
from tests.conftest import QueryChain
from app.routes.tokens import _account_for_user
from types import SimpleNamespace

account_chain = QueryChain([{"account_id": "a1", "account_name": "Main", "created_by": "u1"}])
def table(name):
    return account_chain
client = SimpleNamespace(table=table)
print("Return values:", _account_for_user(client, "u1"))
