from dotenv import load_dotenv
load_dotenv()

from flask import Flask, redirect
from flask_cors import CORS

# Import all blueprints
from app.routes.auth import auth_bp
from app.routes.requester import requester_bp
from app.routes.responder import responder_bp
from app.routes.tokens import tokens_bp

app = Flask(__name__)

# ✅ ADD THIS LINE
CORS(app, origins=["https://ai.gptless.au", "https://ai-preview.gptless.au", "https://ai-api-preview.gptless.au", "http://localhost:3000"])

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(requester_bp)
app.register_blueprint(responder_bp)
app.register_blueprint(tokens_bp)


@app.route("/")
def home():
    return redirect("https://ai-docs.gptless.au")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)