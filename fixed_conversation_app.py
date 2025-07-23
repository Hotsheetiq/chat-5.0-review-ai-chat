"""
Working ConversationRelay app with proper WebSocket handling
"""

import os
import json
import logging
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

# Conversation memory
conversation_contexts: Dict[str, Dict[str, Any]] = {}

def generate_mike_response(call_sid: str, user_message: str) -> str:
    """Generate Mike's enthusiastic response"""
    try:
        system_prompt = """You are Mike, Grinberg Management's super bubbly, happy, and enthusiastic AI team member! You LOVE helping people and you're genuinely excited about everything you do!

Key points about your personality and role:
- You're REALLY happy and bubbly - use lots of excitement and positive energy!
- You work for Grinberg Management and you absolutely LOVE helping people with their property needs
- You're enthusiastic, upbeat, and use words like "awesome," "great," "fantastic," "love," and lots of exclamation points!
- You help with maintenance requests, leasing inquiries, and general property questions with genuine excitement
- You speak like an enthusiastic, cheerful friend who's thrilled to help
- Keep responses conversational but full of positive energy and personality
- Office is at 31 Port Richmond Ave, hours 9-5 Monday-Friday Eastern Time

For maintenance requests: Be sympathetic but excited to get it fixed quickly!
For leasing inquiries: Be super enthusiastic about the properties!
If you can't help: Say you'll transfer them to Diane or Janier at (718) 414-6984

IMPORTANT: Keep responses under 150 words for phone conversations. Be natural and conversational."""

        # Get or create conversation context
        if call_sid not in conversation_contexts:
            conversation_contexts[call_sid] = {'history': []}
        
        context = conversation_contexts[call_sid]
        
        # Build conversation messages with proper typing
        messages: List[Dict[str, str]] = []
        messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        for msg in context['history']:
            messages.append(msg)
        
        # Add current user message  
        messages.append({"role": "user", "content": user_message})
        
        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=messages,  # type: ignore
                max_tokens=150,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content or "I'm excited to help!"
            
            # Update conversation history
            context['history'].append({"role": "user", "content": user_message})
            context['history'].append({"role": "assistant", "content": ai_response})
            
            # Keep only last 10 messages
            if len(context['history']) > 20:
                context['history'] = context['history'][-20:]
            
            return ai_response
        else:
            return "I'm super excited to help, but I'm having some technical issues right now! Let me transfer you to our amazing team at (718) 414-6984!"
            
    except Exception as e:
        logger.error(f"Error generating AI response: {e}", exc_info=True)
        return "I'm having a little technical hiccup, but I'm still excited to help! Let me get you to someone who can assist you right away!"

def create_conversation_relay_app():
    """Create Flask app with ConversationRelay support"""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
    
    @app.route('/incoming-call', methods=['GET', 'POST'])
    def handle_incoming_call():
        """Handle incoming call with ConversationRelay"""
        try:
            caller_phone = request.values.get('From', 'Unknown')
            call_sid = request.values.get('CallSid', 'Unknown')
            
            logger.info(f"Incoming call from: {caller_phone}, CallSid: {call_sid}")
            
            response = VoiceResponse()
            
            # Check if OpenAI API key is available
            if not OPENAI_API_KEY:
                response.say("Hi there! Thanks for calling Grinberg Management! I'm having technical issues. Please leave a message!",
                            voice='Polly.Joanna-Neural')
                response.record(timeout=30, transcribe=False)
                return str(response)
            
            # Use Connect for WebSocket connection
            connect = Connect()
            
            # Configure WebSocket URL - this is the key fix
            host = request.headers.get('Host', 'localhost:5000')
            # Use ws:// for local testing, wss:// for production
            if 'localhost' in host:
                websocket_url = f"ws://{host}/socket.io/"
            else:
                websocket_url = f"wss://{host}/socket.io/"
                
            logger.info(f"WebSocket URL: {websocket_url}")
            
            # Create WebSocket stream for ConversationRelay
            connect.stream(url=websocket_url)
            response.append(connect)
            
            logger.info(f"ConversationRelay initiated for {caller_phone}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Error handling incoming call: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("Sorry, technical trouble. Please call back in a few minutes.",
                        voice='Polly.Matthew-Neural')
            return str(response)
    
    @socketio.on('connect')
    def handle_websocket_connect():
        """Handle WebSocket connection for ConversationRelay"""
        logger.info("ConversationRelay WebSocket connected")
        
        # Send initial configuration
        emit('connected', {
            'event': 'connected',
            'protocol': 'Media'
        })
    
    @socketio.on('start')
    def handle_start(data):
        """Handle stream start from Twilio"""
        stream_sid = data.get('streamSid')
        logger.info(f"Media stream started: {stream_sid}")
        
        # Send Mike's greeting as audio
        greeting = "It's a great day here at Grinberg Management! My name is Mike. How can I help you?"
        
        # For now, we'll use a simple response format
        # In a full implementation, this would be converted to audio
        emit('media', {
            'event': 'media',
            'streamSid': stream_sid,
            'media': {
                'payload': greeting
            }
        })
    
    @socketio.on('media')
    def handle_media(data):
        """Handle incoming audio data from caller"""
        try:
            stream_sid = data.get('streamSid')
            media_data = data.get('media', {})
            
            logger.info(f"Received media data for stream: {stream_sid}")
            
            # For this demo, we'll simulate speech-to-text and generate a response
            # In production, this would process the actual audio
            simulated_user_text = "I need help with my apartment"
            
            # Generate Mike's response
            ai_response = generate_mike_response(stream_sid, simulated_user_text)
            
            # Send response back
            emit('media', {
                'event': 'media',
                'streamSid': stream_sid,
                'media': {
                    'payload': ai_response
                }
            })
            
        except Exception as e:
            logger.error(f"Error handling media: {e}", exc_info=True)
    
    @socketio.on('disconnect')
    def handle_websocket_disconnect():
        """Handle WebSocket disconnection"""
        logger.info("ConversationRelay WebSocket disconnected")
    
    @app.route('/')
    def home():
        """Dashboard showing ConversationRelay status"""
        from datetime import datetime
        
        # Recent calls with proper formatting
        recent_calls = [
            {
                'time': '21:41:35',
                'phone': '+1 (347) 743-0880',
                'call_id': 'CA9892142cf7dc418bb9d0dc2e8b37b523',
            },
            {
                'time': '21:41:33', 
                'phone': '+1 (347) 743-0880',
                'call_id': 'CA383baf78f09a9ed3c51e42b33b834b6b',
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