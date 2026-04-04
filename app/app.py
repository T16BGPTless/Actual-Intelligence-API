"""Main application file."""

from flask import Flask, redirect
from app.routes.auth import auth_bp

app = Flask(__name__)

# Register route groups
app.register_blueprint(auth_bp)

@app.route("/")
def home():
    """Redirects to swagger docs."""
    return redirect("https://docs.gptless.au") # Prefereblly the actual actual intelligence doc

if __name__ == "__main__":
    app.run(debug=True)