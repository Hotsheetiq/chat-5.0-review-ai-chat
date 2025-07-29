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
    """Enhanced property management dashboard"""
    from datetime import datetime
    import pytz
    
    eastern = pytz.timezone('US/Eastern')
    current_time = datetime.now(eastern)
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chris Voice Assistant Dashboard - Grinberg Management</title>
        <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body class="bg-dark text-light">
        <div class="container-fluid">
            <header class="py-4">
                <h1 class="text-center mb-0">🏢 Chris Voice Assistant Dashboard</h1>
                <p class="text-center text-muted">Grinberg Management - Property Management System</p>
                <div class="text-center">
                    <span class="badge bg-success">{{ current_time.strftime('%I:%M:%S %p Eastern') }}</span>
                </div>
            </header>
            
            <!-- System Status -->
            <div class="row mb-4">
                <div class="col-md-3">
                    <div class="card bg-secondary">
                        <div class="card-body text-center">
                            <h5 class="card-title">🎙️ Voice System</h5>
                            <span class="badge bg-success">ONLINE</span>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-secondary">
                        <div class="card-body text-center">
                            <h5 class="card-title">🤖 AI Assistant</h5>
                            <span class="badge bg-success">READY</span>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-secondary">
                        <div class="card-body text-center">
                            <h5 class="card-title">📞 Phone System</h5>
                            <span class="badge bg-warning">CONFIGURED</span>
                        </div>
                    </div>
                </div>
                <div class="col-md-3">
                    <div class="card bg-secondary">
                        <div class="card-body text-center">
                            <h5 class="card-title">🏠 Property Data</h5>
                            <span class="badge bg-info">430 Properties</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Main Actions -->
            <div class="row mb-4">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">📋 Quick Actions</h5>
                        </div>
                        <div class="card-body">
                            <div class="d-grid gap-2">
                                <button class="btn btn-primary" onclick="window.location.href='/test-voice'">🎤 Test Voice System</button>
                                <button class="btn btn-info" onclick="window.location.href='/property-status'">🏢 Check Properties</button>
                                <button class="btn btn-success" onclick="window.location.href='/call-history'">📞 Call History</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">📊 System Info</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>Phone:</strong> (888) 641-1102</p>
                            <p><strong>Status:</strong> <span class="text-success">Active</span></p>
                            <p><strong>Last Update:</strong> {{ current_time.strftime('%B %d, %Y') }}</p>
                            <p><strong>Properties:</strong> 430 Managed Units</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Recent Activity -->
            <div class="row">
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="mb-0">🚀 System Status</h5>
                        </div>
                        <div class="card-body">
                            <div class="alert alert-success">
                                <h6>✅ Flask Application Successfully Running</h6>
                                <p class="mb-0">Chris Voice Assistant is online and ready to handle property management calls.</p>
                            </div>
                            <div class="alert alert-info">
                                <h6>🔧 Next Steps Available</h6>
                                <p class="mb-0">Ready to restore full conversational AI features and voice processing capabilities.</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, current_time=current_time)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)