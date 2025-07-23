"""
Simple working ConversationRelay app without async complications
"""

import os
import json
import logging
from flask import Flask, request, render_template
from flask_socketio import SocketIO, emit
from twilio.twiml.voice_response import VoiceResponse, Connect
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Conversation memory
conversation_contexts = {}

def generate_mike_response(call_sid, user_message):
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
        
        # Build conversation messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in context['history']:
            messages.append(msg)
        
        # Add current user message  
        messages.append({"role": "user", "content": user_message})
        
        if openai_client:
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=messages,
                max_tokens=150,
                temperature=0.8
            )
            
            ai_response = response.choices[0].message.content
            
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
    socketio = SocketIO(app, cors_allowed_origins="*")
    
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
            
            # Use ConversationRelay for human-like AI conversation
            connect = Connect()
            
            # Get the current domain from the request
            host = request.headers.get('Host', 'localhost:5000')
            websocket_url = f"wss://{host}/websocket"
            
            connect.conversation_relay(
                url=websocket_url,
                voice="pNInz6obpgDQGcFmaJgB",  # ElevenLabs Adam voice ID
                tts_provider="elevenlabs"
            )
            
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
        
        # Send initial greeting to ConversationRelay
        emit('message', {
            'event': 'initial_message',
            'text': "It's a great day here at Grinberg Management! My name is Mike. How can I help you?",
            'voice': {
                'provider': 'elevenlabs',
                'voice_id': 'pNInz6obpgDQGcFmaJgB',
                'model': 'eleven_turbo_v2'
            }
        })
    
    @socketio.on('disconnect')
    def handle_websocket_disconnect():
        """Handle WebSocket disconnection"""
        logger.info("ConversationRelay WebSocket disconnected")
    
    @socketio.on('message')
    def handle_websocket_message(data):
        """Handle incoming WebSocket messages from ConversationRelay"""
        try:
            logger.info(f"Received ConversationRelay message: {data}")
            
            # Parse the message
            if isinstance(data, str):
                message = json.loads(data)
            else:
                message = data
                
            event_type = message.get('event')
            call_sid = message.get('callSid', 'default')
            
            if event_type == 'connected':
                logger.info("ConversationRelay connected successfully")
                
            elif event_type == 'media' or event_type == 'user-utterance':
                # Handle incoming speech from caller
                user_text = message.get('text', '')
                if user_text:
                    logger.info(f"User said: {user_text}")
                    
                    # Generate Mike's response
                    ai_response = generate_mike_response(call_sid, user_text)
                    
                    # Send response back to ConversationRelay
                    emit('message', {
                        'event': 'response',
                        'text': ai_response,
                        'voice': {
                            'provider': 'elevenlabs',
                            'voice_id': 'pNInz6obpgDQGcFmaJgB',
                            'model': 'eleven_turbo_v2',
                            'stability': 0.75,
                            'similarity_boost': 0.8
                        }
                    })
                    
            elif event_type == 'user-interrupted':
                logger.info("User interrupted Mike")
                
            elif event_type == 'disconnected':
                logger.info("ConversationRelay disconnected")
                if call_sid in conversation_contexts:
                    del conversation_contexts[call_sid]
                    
        except Exception as e:
            logger.error(f"WebSocket message error: {e}", exc_info=True)
    
    @app.route('/')
    def home():
        """Dashboard showing ConversationRelay status"""
        from datetime import datetime
        
        # Mock recent calls for demo (would be real data from database)
        recent_calls = [
            {
                'time': '21:22:06',
                'phone': '+1 (347) 743-0880',
                'call_id': 'CA5e1c2eba1d5de590de2a31eea38d8392',
            },
            {
                'time': '21:22:04', 
                'phone': '+1 (347) 743-0880',
                'call_id': 'CA82071a2dc0b3f3f8cb860b10cb218e4d',
            }
        ]
        
        return render_template('dashboard.html', 
                             openai_connected=bool(OPENAI_API_KEY),
                             recent_calls=recent_calls)
    
    return app, socketio

if __name__ == '__main__':
    app, socketio = create_conversation_relay_app()
    PORT = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=PORT, debug=True)