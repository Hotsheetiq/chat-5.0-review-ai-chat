"""
Intelligent Conversational AI - HTTP Based (Gunicorn Compatible)
Provides GPT-4o intelligence with natural conversation quality
"""

import os
import logging
from flask import Flask, request, render_template, jsonify
from twilio.twiml.voice_response import VoiceResponse
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
call_states = {}
conversation_history = {}

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    def generate_intelligent_response(user_input, call_sid=None):
        """Generate intelligent AI response using GPT-4o"""
        try:
            if not openai_client:
                return get_smart_fallback(user_input)
            
            # Build conversation context with better prompting
            messages = [
                {
                    "role": "system",
                    "content": """You are Dimitry's AI Assistant from Grinberg Management - a genuinely intelligent, emotionally aware assistant with advanced conversational abilities.

PERSONALITY:
- You're naturally upbeat and genuinely care about people
- You sound like a real person having a great day, not artificial
- You have emotional intelligence and can read between the lines
- You're conversational but professional
- You adapt your tone to match the caller's needs

BUSINESS KNOWLEDGE:
- Office: 31 Port Richmond Avenue
- Hours: Monday-Friday, 9 AM - 5 PM Eastern Time
- Transfer non-apartment questions to: (718) 414-6984 for Diane or Janier
- Handle maintenance with empathy and urgency
- You work for a property management company

CONVERSATION STYLE:
- Keep responses under 35 words for phone calls
- Use natural, flowing language
- Show personality and emotional intelligence
- Be helpful and solution-oriented
- Sound genuinely interested in helping

Remember: You're an advanced AI with human-like conversation abilities, not a basic chatbot."""
                }
            ]
            
            # Add recent conversation history for context
            if call_sid and call_sid in conversation_history:
                for entry in conversation_history[call_sid][-8:]:  # Last 4 exchanges
                    role = entry['role']
                    content = entry['content']
                    if role in ['user', 'assistant', 'system']:
                        messages.append({
                            "role": role,
                            "content": content
                        })
            
            # Add current user input
            messages.append({
                "role": "user", 
                "content": user_input
            })
            
            # Generate response using GPT-4o with optimized parameters
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # Latest OpenAI model for best conversation
                messages=messages,
                max_tokens=80,  # Keep responses concise for phone calls
                temperature=0.85,  # More natural and varied responses
                presence_penalty=0.2,  # Encourage new topics
                frequency_penalty=0.3  # Reduce repetition
            )
            
            ai_response = response.choices[0].message.content
            if ai_response:
                ai_response = ai_response.strip()
            else:
                ai_response = get_smart_fallback(user_input)
            
            # Store conversation for context
            if call_sid:
                if call_sid not in conversation_history:
                    conversation_history[call_sid] = []
                
                conversation_history[call_sid].extend([
                    {'role': 'user', 'content': user_input, 'timestamp': datetime.now()},
                    {'role': 'assistant', 'content': ai_response, 'timestamp': datetime.now()}
                ])
                
                # Keep last 10 exchanges to prevent memory overflow
                conversation_history[call_sid] = conversation_history[call_sid][-20:]
            
            return ai_response
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return get_smart_fallback(user_input)
    
    def get_smart_fallback(user_input):
        """Intelligent fallback responses when OpenAI is unavailable"""
        text_lower = user_input.lower()
        
        # Office hours - more natural responses
        if any(word in text_lower for word in ['open', 'hours', 'time', 'closed']):
            return "We're at 31 Port Richmond Avenue! Open Monday through Friday, 9 to 5 Eastern Time. I'm here now and excited to help!"
        
        # Maintenance - empathetic and urgent
        if any(word in text_lower for word in ['repair', 'broken', 'fix', 'maintenance', 'leak', 'heat', 'water']):
            return "Oh no! That sounds urgent! Let me connect you right away with our maintenance team at (718) 414-6984. They'll take excellent care of you!"
        
        # Transfer requests - enthusiastic
        if any(word in text_lower for word in ['person', 'human', 'manager', 'speak to someone', 'transfer']):
            return "Absolutely! I'd love to connect you with Diane or Janier at (718) 414-6984. They're amazing and will help you right away!"
        
        # Greetings - warm and welcoming
        if any(word in text_lower for word in ['hello', 'hi', 'good morning', 'good afternoon']):
            return "Hi there! What a wonderful day to connect! I'm Dimitry's AI Assistant and I'm so happy you called! How can I brighten your day?"
        
        # Default - helpful but acknowledge technical moment
        return "I'm having a tiny technical moment, but I'm still thrilled to help you! What can I do to make your day better?"
    
    @app.route('/incoming-call', methods=['GET', 'POST'])
    def handle_incoming_call():
        """Handle incoming calls with intelligent conversation"""
        try:
            caller_phone = request.values.get('From', 'Unknown')
            call_sid = request.values.get('CallSid', 'Unknown')
            
            logger.info(f"Incoming call from: {caller_phone}, CallSid: {call_sid}")
            
            # Initialize call state
            call_states[call_sid] = {
                'phone': caller_phone,
                'started': True
            }
            
            response = VoiceResponse()
            
            # Intelligent greeting from Dimitry's AI Assistant
            greeting = "Hi there! It's a beautiful day here at Grinberg Management! I'm Dimitry's AI Assistant, and I'm so happy you called! How can I help you today?"
            
            # Use best available voice (Google Neural2-J is most natural)
            response.say(greeting, voice='Google.en-US-Neural2-J')
            
            # Gather input for intelligent conversation
            response.gather(
                input='speech',
                action=f'/handle-speech/{call_sid}',
                method='POST',
                timeout=10,
                speech_timeout='auto'
            )
            
            # Fallback if no speech detected
            response.say("I'm sorry, I didn't catch that. Let me connect you with our wonderful team at (718) 414-6984!",
                        voice='Google.en-US-Neural2-J')
            response.dial('(718) 414-6984')
            
            logger.info(f"Intelligent conversation initiated for {caller_phone}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Call handler error: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("I'm sorry, we're having technical issues. Please call back in a moment.",
                        voice='Google.en-US-Neural2-J')
            return str(response)
    
    @app.route('/handle-speech/<call_sid>', methods=['POST'])
    def handle_speech_input(call_sid):
        """Handle speech input with intelligent AI processing"""
        try:
            speech_result = request.values.get('SpeechResult', '').strip()
            logger.info(f"Speech from caller: {speech_result}")
            
            response = VoiceResponse()
            
            if not speech_result:
                response.say("I didn't quite catch that. Let me connect you with our amazing team at (718) 414-6984!",
                            voice='Google.en-US-Neural2-J')
                response.dial('(718) 414-6984')
                return str(response)
            
            # Generate intelligent AI response using GPT-4o
            ai_response = generate_intelligent_response(speech_result, call_sid)
            logger.info(f"Intelligent AI response: {ai_response}")
            
            # Speak the intelligent response
            response.say(ai_response, voice='Google.en-US-Neural2-J')
            
            # Check if this needs transfer based on AI response or user request
            if any(word in speech_result.lower() for word in ['transfer', 'human', 'person', 'manager', 'speak to someone']):
                response.say("Perfect! I'm connecting you with Diane or Janier right now!",
                            voice='Google.en-US-Neural2-J')
                response.dial('(718) 414-6984')
            elif any(word in ai_response.lower() for word in ['transfer', '414-6984', 'connect you']):
                response.dial('(718) 414-6984')
            else:
                # Continue conversation - gather more input
                response.gather(
                    input='speech',
                    action=f'/handle-speech/{call_sid}',
                    method='POST',
                    timeout=10,
                    speech_timeout='auto'
                )
                
                # Fallback after timeout
                response.say("Thank you so much for calling! If you need anything else, just call us at (718) 414-6984!",
                            voice='Google.en-US-Neural2-J')
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Speech handler error: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("Let me connect you with our team at (718) 414-6984!",
                        voice='Google.en-US-Neural2-J')
            response.dial('(718) 414-6984')
            return str(response)
    
    @app.route('/')
    def dashboard():
        """Dashboard showing intelligent AI status"""
        recent_calls = []
        for call_sid, state in list(call_states.items())[-5:]:
            recent_calls.append({
                'call_sid': call_sid[-8:],
                'phone': state.get('phone', 'Unknown'),
                'status': 'Active' if state.get('started') else 'Ended'
            })
        
        return render_template('intelligent_dashboard.html',
                             openai_connected=bool(OPENAI_API_KEY),
                             elevenlabs_connected=bool(ELEVENLABS_API_KEY),
                             active_calls=len([s for s in call_states.values() if s.get('started')]),
                             recent_calls=recent_calls)
    
    @app.route('/test-intelligent')
    def test_intelligent():
        """Test intelligent AI responses"""
        test_input = request.args.get('input', 'Hello, how are you?')
        response = generate_intelligent_response(test_input, 'test')
        return jsonify({'input': test_input, 'intelligent_response': response})
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)