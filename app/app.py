from flask import Flask, redirect

# Import all blueprints
from app.routes.auth import auth_bp
from app.routes.requester import requester_bp
from app.routes.responder import responder_bp
from app.routes.tokens import tokens_bp

app = Flask(__name__)

# Register all blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(requester_bp)
app.register_blueprint(responder_bp)
app.register_blueprint(tokens_bp)

@app.route("/")
def home():
    """Redirects to swagger docs."""
    return redirect("https://docs.gptless.au") # Prefereblly the actual actual intelligence doc

if __name__ == "__main__":
    app.run(debug=True)