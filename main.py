# Import working Media Stream app with proper Twilio protocol
from working_media_stream_app import create_conversation_relay_app

# Create app with correct Twilio Media Streams implementation
app, socketio = create_conversation_relay_app()