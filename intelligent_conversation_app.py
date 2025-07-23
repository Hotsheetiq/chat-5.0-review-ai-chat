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
                logger.error("No OpenAI client available")
                return get_smart_fallback(user_input)
            
            logger.info(f"Generating GPT-4o response for: {user_input}")
            
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
- Respond like ChatGPT - intelligent, thoughtful, and genuinely conversational
- Keep responses under 35 words for phone calls but be natural and complete
- Use your full AI capabilities - reasoning, understanding, and personality
- Be helpful and solution-oriented with real intelligence
- Sound like you're truly understanding and thinking about their request

Remember: You are a full GPT-4o AI assistant, not a simple chatbot. Use your complete intelligence and reasoning abilities."""
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
            
            logger.info(f"GPT-4o response: {ai_response}")
            return ai_response
        
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            # Try one more time with simpler prompt for robustness
            if openai_client:
                try:
                    response = openai_client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are Dimitry's AI Assistant from Grinberg Management. Be helpful and conversational. Keep responses under 30 words."},
                            {"role": "user", "content": user_input}
                        ],
                        max_tokens=60,
                        temperature=0.7
                    )
                    ai_response = response.choices[0].message.content
                    if ai_response:
                        ai_response = ai_response.strip()
                        logger.info(f"GPT-4o fallback response: {ai_response}")
                        return ai_response
                except Exception as e2:
                    logger.error(f"Second OpenAI attempt failed: {e2}")
            return get_smart_fallback(user_input)
    
    def get_enhanced_fallback(user_input, call_sid=None):
        """Enhanced fallback with conversation context awareness"""
        # Check if we've responded to similar queries recently
        if call_sid and call_sid in conversation_history:
            recent_responses = [entry['content'] for entry in conversation_history[call_sid] 
                             if entry['role'] == 'assistant']
            
            # Generate response and ensure it's different from recent ones
            max_attempts = 3
            for _ in range(max_attempts):
                response = get_smart_fallback(user_input)
                # Check if this response is too similar to recent ones
                if not any(response[:20] in recent_resp for recent_resp in recent_responses[-3:]):
                    # Store this response for future reference
                    if call_sid not in conversation_history:
                        conversation_history[call_sid] = []
                    conversation_history[call_sid].extend([
                        {'role': 'user', 'content': user_input, 'timestamp': datetime.now()},
                        {'role': 'assistant', 'content': response, 'timestamp': datetime.now()}
                    ])
                    return response
        
        return get_smart_fallback(user_input)
    
    def get_smart_fallback(user_input):
        """Intelligent fallback responses with variation to prevent repetition"""
        text_lower = user_input.lower()
        
        import random
        
        # Office hours - varied natural responses
        if any(word in text_lower for word in ['open', 'hours', 'time', 'closed']):
            responses = [
                "We're right here at 31 Port Richmond Avenue! Our doors are open Monday through Friday, 9 AM to 5 PM Eastern. I'm available right now to help with anything!",
                "You can find us at 31 Port Richmond Avenue! We're here Monday to Friday, 9 to 5 Eastern Time. I'm here and ready to assist you today!",
                "Our office is at 31 Port Richmond Avenue, and we're open weekdays from 9 AM to 5 PM Eastern. I'm here now and would love to help!"
            ]
            return random.choice(responses)
        
        # Maintenance - empathetic with urgency variations
        if any(word in text_lower for word in ['repair', 'broken', 'fix', 'maintenance', 'leak', 'heat', 'water', 'emergency']):
            responses = [
                "That sounds really urgent! I want to get you help immediately. Let me connect you with our maintenance team at (718) 414-6984 - they're fantastic!",
                "Oh my, that needs attention right away! I'm connecting you directly to our maintenance experts at (718) 414-6984. They'll prioritize your issue!",
                "I'm so sorry you're dealing with that! This needs immediate attention. Our skilled maintenance team at (718) 414-6984 will take excellent care of you!"
            ]
            return random.choice(responses)
        
        # Transfer requests - enthusiastic variations
        if any(word in text_lower for word in ['person', 'human', 'manager', 'speak to someone', 'transfer']):
            responses = [
                "Perfect! I'd be delighted to connect you with Diane or Janier at (718) 414-6984. They're wonderful people who'll give you personalized attention!",
                "Absolutely! Let me get you directly to Diane or Janier at (718) 414-6984. They're incredibly helpful and will take great care of you!",
                "Of course! I'll connect you right now with our amazing team members Diane or Janier at (718) 414-6984. They'll be thrilled to help!"
            ]
            return random.choice(responses)
        
        # Greetings - warm variations
        if any(word in text_lower for word in ['hello', 'hi', 'good morning', 'good afternoon', 'hey']):
            responses = [
                "Hello! It's such a pleasure to hear from you! I'm Dimitry's AI Assistant, and I'm genuinely excited to help make your day better!",
                "Hi there! What a wonderful day to connect! I'm Dimitry's AI Assistant, and I'm absolutely delighted you called! How can I assist you?",
                "Good day! I'm Dimitry's AI Assistant, and I'm so happy you reached out! I'm here and ready to help with whatever you need!"
            ]
            return random.choice(responses)
        
        # Questions about services
        if any(word in text_lower for word in ['rent', 'apartment', 'lease', 'payment']):
            responses = [
                "I'd be happy to help with your housing questions! For detailed assistance with rent, leases, or payments, let me connect you with Diane or Janier at (718) 414-6984!",
                "Great question about your apartment! Our specialists Diane and Janier at (718) 414-6984 have all the details and can provide personalized assistance!",
                "I want to make sure you get the most accurate information about your housing needs! Diane or Janier at (718) 414-6984 are the perfect people to help you!"
            ]
            return random.choice(responses)
        
        # Default - helpful with personality variations
        default_responses = [
            "I'm having a brief technical moment, but I'm still absolutely thrilled to help you! What can I do to brighten your day?",
            "Even with a tiny technical hiccup, I'm here and excited to assist you! Tell me how I can make your experience wonderful!",
            "Despite a small technical pause, I'm completely focused on helping you! What would make your day better right now?"
        ]
        return random.choice(default_responses)
    
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