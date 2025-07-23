"""
True Conversational AI Implementation with ConversationRelay
This provides genuine AI conversation with WebSocket integration
"""

import os
import logging
from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, emit
from twilio.twiml.voice_response import VoiceResponse, Connect
from openai import OpenAI
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Call state tracking
active_calls = {}
conversation_history = {}

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    @app.route('/incoming-call', methods=['GET', 'POST'])
    def handle_incoming_call():
        """Handle incoming calls with true conversational AI using ConversationRelay"""
        try:
            caller_phone = request.values.get('From', 'Unknown')
            call_sid = request.values.get('CallSid', 'Unknown')
            
            logger.info(f"Incoming call from: {caller_phone}, CallSid: {call_sid}")
            
            # Get the base URL for WebSocket
            base_url = request.host_url.replace('http://', 'wss://').replace('https://', 'wss://').rstrip('/')
            websocket_url = f"{base_url}/websocket"
            
            response = VoiceResponse()
            
            # Use ConversationRelay for true conversational AI
            connect = Connect()
            
            # ConversationRelay TwiML with proper syntax
            connect.conversation_relay(
                url=websocket_url,
                welcome_greeting="Hi there! It's a beautiful day here at Grinberg Management! I'm Dimitry's AI Assistant, and I'm so happy you called! How can I help you today?"
            )
            
            response.append(connect)
            
            logger.info(f"ConversationRelay initiated for {caller_phone} -> {websocket_url}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Call handler error: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("I'm sorry, we're having technical issues. Please call back in a moment.")
            return str(response)
    
    @socketio.on('connect')
    def handle_websocket_connect():
        """Handle WebSocket connection for conversational AI"""
        logger.info("ConversationRelay WebSocket connected")
        emit('status', {'message': 'Connected to Dimitry\'s AI Assistant'})
    
    @socketio.on('disconnect')
    def handle_websocket_disconnect():
        """Handle WebSocket disconnection"""
        logger.info("ConversationRelay WebSocket disconnected")
    
    @socketio.on('message')
    def handle_websocket_message(data):
        """Handle messages from ConversationRelay"""
        try:
            if isinstance(data, str):
                data = json.loads(data)
            
            logger.info(f"Received WebSocket message: {data}")
            handle_conversation_event(data)
            
        except Exception as e:
            logger.error(f"WebSocket message error: {e}", exc_info=True)
    
    def handle_conversation_event(data):
        """Handle conversation events from ConversationRelay"""
        event_type = data.get('type')
        call_sid = data.get('callSid', 'unknown')
        
        if event_type == 'setup':
            # Initialize conversation
            active_calls[call_sid] = {
                'started_at': datetime.now(),
                'phone': data.get('from', 'Unknown')
            }
            conversation_history[call_sid] = []
            
            logger.info(f"Call setup for {call_sid}")
            
        elif event_type == 'prompt':
            # User spoke - generate AI response
            user_text = data.get('voicePrompt', '')
            logger.info(f"User said: {user_text}")
            
            # Add to conversation history
            conversation_history[call_sid].append({
                'role': 'user',
                'content': user_text,
                'timestamp': datetime.now()
            })
            
            # Generate intelligent AI response
            ai_response = generate_intelligent_response(call_sid, user_text)
            
            # Add AI response to history
            conversation_history[call_sid].append({
                'role': 'assistant',
                'content': ai_response,
                'timestamp': datetime.now()
            })
            
            # Send response back to ConversationRelay
            emit('response', {
                'type': 'response',
                'response': ai_response
            })
            
            logger.info(f"AI responded: {ai_response}")
            
        elif event_type == 'interrupt':
            # User interrupted - handle gracefully
            logger.info(f"User interrupted in call {call_sid}")
            
        elif event_type == 'end':
            # Call ended
            logger.info(f"Call {call_sid} ended")
            if call_sid in active_calls:
                del active_calls[call_sid]
            if call_sid in conversation_history:
                del conversation_history[call_sid]
    
    def generate_intelligent_response(call_sid, user_input):
        """Generate intelligent AI response using OpenAI"""
        try:
            if not openai_client:
                return get_smart_fallback(user_input)
            
            # Build conversation context
            messages = [
                {
                    "role": "system",
                    "content": """You are Dimitry's AI Assistant from Grinberg Management - a genuinely intelligent, helpful, and naturally upbeat assistant. You have human-like conversation abilities and emotional intelligence.

Key traits:
- Sound like a real person having a great day, not artificial
- Be naturally helpful and genuinely care about solving problems
- Use conversational language, not robotic responses
- Show personality and emotional intelligence
- Keep responses conversational but informative (under 40 words)

Business info:
- Office: 31 Port Richmond Avenue
- Hours: Monday-Friday, 9 AM - 5 PM Eastern Time
- Transfer non-apartment questions to: (718) 414-6984 for Diane or Janier
- Handle maintenance requests with empathy and urgency

Remember: You're an intelligent AI assistant, not a basic chatbot. Engage naturally!"""
                }
            ]
            
            # Add recent conversation history
            if call_sid in conversation_history:
                for entry in conversation_history[call_sid][-6:]:  # Last 3 exchanges
                    messages.append({
                        "role": entry['role'],
                        "content": entry['content']
                    })
            
            # Add current user input
            messages.append({
                "role": "user", 
                "content": user_input
            })
            
            # Generate response using GPT-4o (latest model)
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # Latest OpenAI model for best conversation
                messages=messages,
                max_tokens=100,
                temperature=0.8,  # More natural and varied responses
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return get_smart_fallback(user_input)
    
    def get_smart_fallback(user_input):
        """Smart fallback responses when OpenAI is unavailable"""
        text_lower = user_input.lower()
        
        # Office hours
        if any(word in text_lower for word in ['open', 'hours', 'time', 'closed']):
            return "Our office is at 31 Port Richmond Avenue! We're open Monday through Friday, 9 to 5 Eastern Time. I'm here and happy to help however I can!"
        
        # Maintenance
        if any(word in text_lower for word in ['repair', 'broken', 'fix', 'maintenance', 'leak', 'heat']):
            return "Oh no! I'm so sorry you're having that issue! Let me get you connected right away with our maintenance team at (718) 414-6984. They'll take great care of you!"
        
        # Transfer requests
        if any(word in text_lower for word in ['person', 'human', 'manager', 'speak to someone']):
            return "Absolutely! I'd be happy to connect you with Diane or Janier right now at (718) 414-6984. They're wonderful!"
        
        # Default
        return "I'm having a tiny technical moment, but I'm still so excited to help you! What can I do for you today?"
    
    @app.route('/')
    def dashboard():
        """Dashboard showing conversational AI status"""
        return render_template('conversational_dashboard.html',
                             openai_connected=bool(OPENAI_API_KEY),
                             elevenlabs_connected=bool(ELEVENLABS_API_KEY),
                             active_calls=len(active_calls))
    
    @app.route('/test-conversation')
    def test_conversation():
        """Test conversational AI responses"""
        test_input = request.args.get('input', 'Hello, how are you?')
        response = generate_intelligent_response('test', test_input)
        return jsonify({'input': test_input, 'ai_response': response})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)