# Import Flask app for gunicorn compatibility
# Import the ConversationRelay app instead of basic TTS app
from conversational_ai import create_conversation_relay_app
import os

# Create the ConversationRelay app with real human-like AI conversation
app, socketio = create_conversation_relay_app()

# This file exists for compatibility with the gunicorn workflow
# The actual application is in app.py