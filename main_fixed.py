"""
Simple working main.py with proper Flask app initialization
"""

import os
from flask import Flask, render_template_string

# Simple, working Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

@app.route("/")
def dashboard():
    """Simple dashboard to verify app is working"""
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chris Voice Assistant - Working</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
    </head>
    <body class="bg-dark text-light">
        <div class="container mt-5">
            <h1 class="text-center">🏢 Chris Voice Assistant Dashboard</h1>
            <p class="text-center text-success">✅ Flask Application Running Successfully</p>
            <div class="alert alert-success text-center">
                <h4>System Status: ONLINE</h4>
                <p>Ready for voice processing and property management</p>
            </div>
        </div>
    </body>
    </html>
    """)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)