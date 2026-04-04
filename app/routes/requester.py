from flask import Blueprint

requester_bp = Blueprint("requester", __name__)

@requester_bp.route("/v1/requester/test")
def test():
    return "Requester works!"