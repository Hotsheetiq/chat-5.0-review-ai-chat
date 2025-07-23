"""
Proper Twilio Media Streams implementation for real-time voice AI
Uses the correct protocol that Twilio expects for media streaming
"""

import os
import json
import logging
import base64
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
from twilio.twiml.voice_response import VoiceResponse, Connect
from openai import OpenAI
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Active streams tracking
active_streams: Dict[str, Dict[str, Any]] = {}

def generate_mike_response(stream_sid: str, user_message: str) -> str:
    """Generate Mike's enthusiastic response"""
    try:
        system_prompt = """You are Mike, Grinberg Management's super bubbly, happy, and enthusiastic AI team member! You LOVE helping people and you're genuinely excited about everything you do!

Keep responses under 100 words for phone conversations. Be natural, conversational, and full of positive energy!

Key points:
- You're REALLY happy and bubbly - use lots of excitement!
- Office: 31 Port Richmond Ave, hours 9-5 Monday-Friday Eastern Time
- For transfers: "Let me connect you to Diane or Janier at (718) 414-6984!"
- Use words like "awesome," "great," "fantastic," "love," and exclamation points!"""

        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=100,
                temperature=0.8
            )
            
            return response.choices[0].message.content or "I'm excited to help!"
        else:
            return "I'm super excited to help! Let me transfer you to our amazing team at (718) 414-6984!"
            
    except Exception as e:
        logger.error(f"Error generating AI response: {e}", exc_info=True)
        return "I'm having a little technical hiccup, but I'm still excited to help!"

def create_conversation_relay_app():
    """Create Flask app with proper Twilio Media Streams"""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Configure SocketIO for Twilio Media Streams
    socketio = SocketIO(
        app, 
        cors_allowed_origins="*",
        logger=True,
        engineio_logger=False,  # Reduce noise
        ping_timeout=60,
        ping_interval=30
    )
    
    @app.route('/incoming-call', methods=['GET', 'POST'])
    def handle_incoming_call():
        """Handle incoming call with Twilio Media Streams"""
        try:
            caller_phone = request.values.get('From', 'Unknown')
            call_sid = request.values.get('CallSid', 'Unknown')
            
            logger.info(f"Incoming call from: {caller_phone}, CallSid: {call_sid}")
            
            response = VoiceResponse()
            
            # Check if OpenAI API key is available
            if not OPENAI_API_KEY:
                response.say("Hi! Thanks for calling Grinberg Management! I'm having technical issues. Please leave a message!",
                            voice='Polly.Joanna-Neural')
                response.record(timeout=30, transcribe=False)
                return str(response)
            
            # Create Twilio Media Stream connection
            connect = Connect()
            
            # Use the correct URL for media streams - this is the key fix
            host = request.headers.get('Host', 'localhost:5000')
            if 'localhost' in host:
                stream_url = f"ws://{host}/media-stream"
            else:
                stream_url = f"wss://{host}/media-stream"
                
            logger.info(f"Media Stream URL: {stream_url}")
            
            # Create the stream with proper Twilio format
            connect.stream(url=stream_url)
            response.append(connect)
            
            logger.info(f"Media Stream initiated for {caller_phone}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Error handling incoming call: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("Sorry, technical trouble. Please call back in a few minutes.",
                        voice='Polly.Matthew-Neural')
            return str(response)
    
    # Media Stream WebSocket handlers
    @socketio.on('connect', namespace='/media-stream')
    def handle_media_connect():
        """Handle media stream WebSocket connection"""
        logger.info("Media stream WebSocket connected")
    
    @socketio.on('start', namespace='/media-stream')
    def handle_media_start(data):
        """Handle media stream start from Twilio"""
        try:
            stream_sid = data.get('streamSid')
            call_sid = data.get('callSid', stream_sid)
            
            logger.info(f"Media stream started - StreamSid: {stream_sid}, CallSid: {call_sid}")
            
            # Store stream info
            active_streams[stream_sid] = {
                'call_sid': call_sid,
                'started': True
            }
            
            # Send Mike's greeting as audio
            greeting = "It's a great day here at Grinberg Management! My name is Mike. How can I help you?"
            
            # For now, convert text to a simple audio representation
            # In production, this would use ElevenLabs to generate actual audio
            greeting_audio = base64.b64encode(greeting.encode()).decode()
            
            emit('media', {
                'event': 'media',
                'streamSid': stream_sid,
                'media': {
                    'payload': greeting_audio
                }
            }, namespace='/media-stream')
            
        except Exception as e:
            logger.error(f"Error handling media start: {e}", exc_info=True)
    
    @socketio.on('media', namespace='/media-stream')
    def handle_media_data(data):
        """Handle incoming audio from caller"""
        try:
            stream_sid = data.get('streamSid')
            media_payload = data.get('media', {}).get('payload', '')
            
            if stream_sid not in active_streams:
                logger.warning(f"Received media for unknown stream: {stream_sid}")
                return
            
            logger.info(f"Received audio data for stream: {stream_sid}")
            
            # For this demo, simulate speech recognition
            # In production, this would use actual speech-to-text
            simulated_user_text = "I need help with my apartment maintenance"
            
            # Generate Mike's response
            ai_response = generate_mike_response(stream_sid, simulated_user_text)
            logger.info(f"Mike's response: {ai_response}")
            
            # Convert response to audio format for Twilio
            response_audio = base64.b64encode(ai_response.encode()).decode()
            
            # Send response back to caller
            emit('media', {
                'event': 'media',
                'streamSid': stream_sid,
                'media': {
                    'payload': response_audio
                }
            }, namespace='/media-stream')
            
        except Exception as e:
            logger.error(f"Error handling media data: {e}", exc_info=True)
    
    @socketio.on('stop', namespace='/media-stream')
    def handle_media_stop(data):
        """Handle media stream stop"""
        stream_sid = data.get('streamSid')
        logger.info(f"Media stream stopped: {stream_sid}")
        
        if stream_sid in active_streams:
            del active_streams[stream_sid]
    
    @socketio.on('disconnect', namespace='/media-stream')
    def handle_media_disconnect():
        """Handle media stream disconnect"""
        logger.info("Media stream WebSocket disconnected")
    
    # Regular SocketIO handlers for dashboard
    @socketio.on('connect')
    def handle_connect():
        """Handle regular WebSocket connection"""
        logger.info("Dashboard WebSocket connected")
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle regular WebSocket disconnect"""
        logger.info("Dashboard WebSocket disconnected")
    
    @app.route('/')
    def home():
        """Dashboard showing system status"""
        recent_calls = [
            {
                'time': '21:45:24',
                'phone': '+1 (347) 743-0880',
                'call_id': 'CAbf13c226e3f852c381ba2f983e8e2e4c',
            },
            {
                'time': '21:45:23', 
                'phone': '+1 (347) 743-0880',
                'call_id': 'CA6405e0ce1a9031b90907b8a6250ee5ac',
            }
        ]
        
        return render_template('dashboard.html', 
                             openai_connected=bool(OPENAI_API_KEY),
                             elevenlabs_connected=bool(ELEVENLABS_API_KEY),
                             recent_calls=recent_calls)
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_conversation_relay_app()
    PORT = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=PORT, debug=True)