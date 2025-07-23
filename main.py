# Import Flask app for gunicorn compatibility
from app import app

# This file exists for compatibility with the gunicorn workflow
# The actual application is in app.py