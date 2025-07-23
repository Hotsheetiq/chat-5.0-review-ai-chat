# Import fixed ConversationRelay app
from fixed_conversation_app import create_conversation_relay_app

# Create the ConversationRelay app with proper WebSocket handling
app, socketio = create_conversation_relay_app()