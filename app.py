import os
import json
import base64
import asyncio
import logging
import websockets
from threading import Thread
from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, emit, disconnect
from twilio.twiml.voice_response import VoiceResponse, Connect
from rent_manager import RentManagerAPI
from property_data import PropertyDataManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
RENT_MANAGER_API_KEY = os.getenv('RENT_MANAGER_API_KEY')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
PORT = int(os.getenv('PORT', 5000))

# Initialize Flask app with SocketIO
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize services
rent_manager = RentManagerAPI(RENT_MANAGER_API_KEY) if RENT_MANAGER_API_KEY else None
property_data = PropertyDataManager()

# Validate environment variables (warnings only for now)
if not OPENAI_API_KEY:
    logger.warning('OPENAI_API_KEY not found. Voice assistant will be disabled until key is provided.')

if not RENT_MANAGER_API_KEY:
    logger.warning('RENT_MANAGER_API_KEY not found. Rent Manager integration will be disabled.')

if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
    logger.warning('Twilio credentials not found. Some features may be limited.')

@app.route('/')
def home():
    """Serve the dashboard page."""
    return render_template('dashboard.html')

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy", 
        "message": "Property Management Voice Assistant is running",
        "services": {
            "openai": bool(OPENAI_API_KEY),
            "rent_manager": bool(rent_manager),
            "twilio": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)
        }
    })

@app.route('/incoming-call', methods=['GET', 'POST'])
def handle_incoming_call():
    """Handle incoming call and return TwiML response."""
    try:
        # Get caller information from Twilio
        caller_phone = request.values.get('From', 'Unknown')
        
        logger.info(f"Incoming call from: {caller_phone}")
        
        response = VoiceResponse()
        
        # Check if OpenAI API key is available
        if not OPENAI_API_KEY:
            response.say("Thank you for calling our property management office. "
                        "Our AI assistant is currently unavailable for maintenance. "
                        "Please call back later or leave a message after the beep.")
            response.record(timeout=30, transcribe=False)
            return str(response)
        
        # Happy American greeting with natural speech patterns
        greeting = "It's a great day at Grinberg Management,<break time='0.4s'/> this is Sarah!<break time='0.3s'/> How can I help you today?"
        response.say(greeting, voice='Polly.Kimberly-Neural', language='en-US')
        
        # Use speech gathering instead of media streaming for better reliability
        gather = response.gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action='/process-speech',
            method='POST'
        )
        
        # Fallback if no speech detected - happy American voice
        response.say("Oops! I didn't catch that. Give me a call back and try again!",
                    voice='Polly.Kimberly-Neural', language='en-US')
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, we're experiencing technical difficulties. Please try calling back later.")
        return str(response)

@app.route('/fallback-call', methods=['POST'])
def fallback_call():
    """Fallback handler in case primary webhook fails."""
    try:
        logger.warning("Fallback handler activated")
        response = VoiceResponse()
        
        # Bubbly fallback message from Sarah
        create_natural_say(response, "Hey! This is Sarah from Grinberg Management. "
                    "We're having some technical issues right now, but I still want to help! "
                    "Please call back in a few minutes, or leave me a message after the beep "
                    "with your name, number, and what you need - I'll make sure someone gets back to you!")
        
        # Record message for follow-up
        response.record(
            timeout=60,
            max_length=300,
            transcribe=True,
            transcribe_callback=f"{request.host_url}transcription"
        )
        
        create_natural_say(response, "Thank you for your message. We'll get back to you as soon as possible.")
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error in fallback handler: {e}")
        # Absolute last resort
        response = VoiceResponse()
        response.say("We apologize for the inconvenience. Please call back later.")
        return str(response)

@app.route('/transcription', methods=['POST'])
def handle_transcription():
    """Handle transcription callbacks from recorded messages."""
    try:
        transcription_text = request.form.get('TranscriptionText', '')
        caller_phone = request.form.get('From', 'Unknown')
        recording_url = request.form.get('RecordingUrl', '')
        
        logger.info(f"Transcription received from {caller_phone}: {transcription_text}")
        
        # In production, you'd store this for follow-up
        # For now, just log it
        
        return 'Transcription received', 200
        
    except Exception as e:
        logger.error(f"Error handling transcription: {e}")
        return 'Error', 500

@app.route('/process-speech', methods=['POST'])
def process_speech():
    """Process speech input from caller."""
    try:
        # Get speech result from Twilio
        speech_result = request.values.get('SpeechResult', '')
        caller_phone = request.values.get('From', 'Unknown')
        
        logger.info(f"Speech from {caller_phone}: {speech_result}")
        
        response = VoiceResponse()
        
        if not speech_result:
            response.say("I didn't catch that. Could you please repeat your request?",
                        voice='Polly.Kimberly-Neural', language='en-US')
            response.gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action='/process-speech',
                method='POST'
            )
            return str(response)
        
        # Use OpenAI for intelligent response generation
        try:
            ai_response = generate_ai_response(speech_result, caller_phone)
            create_natural_say(response, ai_response)
        except Exception as ai_error:
            logger.error(f"OpenAI error: {ai_error}")
            # Fallback to basic keyword processing with natural voice
            speech_lower = speech_result.lower()
            
            if any(word in speech_lower for word in ['maintenance', 'repair', 'broken', 'fix']):
                create_natural_say(response, "Oh no! I'm so sorry you're having that issue! "
                            "I'm creating a service ticket for you right now - our awesome maintenance team "
                            "will take care of you within 24 hours! Anything else I can help with?")
                            
            elif any(word in speech_lower for word in ['lease', 'rent', 'available', 'apartment']):
                create_natural_say(response, "That's so exciting! I'd love to help you find a great place! "
                            "I'm setting up a follow-up for our leasing team - they'll reach out within one business day "
                            "with all the info about our available units! What else can I help you with?")
                            
            elif any(word in speech_lower for word in ['hours', 'office', 'contact']):
                hours_info = property_data.get_office_hours()
                create_natural_say(response, f"Great question! Our Grinberg Management office hours are {hours_info}. "
                            "Anything else I can help you with today?")
                            
            else:
                create_natural_say(response, "Thanks so much for calling Grinberg Management! I've totally got this covered - "
                            "someone from our awesome team will follow up with you super soon! "
                            "Anything else I can help you with today?")
        
        # Give option to continue or end call
        response.gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/process-speech',
            method='POST'
        )
        
        create_natural_say(response, "Thank you for calling. Have a great day!")
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I had trouble processing your request. "
                    "Please call back and try again.")
        return str(response)

# Conversation memory to avoid repetition
conversation_memory = {}

def get_intelligent_response(user_input, caller_phone):
    """Intelligent response system that adapts and doesn't repeat itself."""
    user_lower = user_input.lower().strip()
    
    # Initialize conversation memory for this caller
    if caller_phone not in conversation_memory:
        conversation_memory[caller_phone] = {
            'topics_discussed': set(),
            'questions_asked': [],
            'conversation_stage': 'greeting'
        }
    
    memory = conversation_memory[caller_phone]
    
    # AI/Human identity questions - vary responses
    if any(word in user_lower for word in ['human', 'real person', 'real', 'robot', 'ai', 'computer', 'bot']):
        if 'identity' not in memory['topics_discussed']:
            memory['topics_discussed'].add('identity')
            return "I'm an AI assistant, but I'm here to help you just like any team member would! What do you need help with today?"
        else:
            return "Yep, still your friendly AI assistant! Now, what can I actually help you with?"
    
    # Location/office questions with specific help
    elif any(word in user_lower for word in ['where', 'located', 'address', 'office', 'location']):
        if 'location' not in memory['topics_discussed']:
            memory['topics_discussed'].add('location')
            return "We manage properties throughout the area. Are you a current tenant needing to reach us, or are you interested in viewing available apartments? That'll help me point you in the right direction."
        else:
            return "Which specific location do you need? Are you looking for our leasing office or need to know about a specific property address?"
    
    # Maintenance requests - get specific
    elif any(word in user_lower for word in ['fix', 'broken', 'maintenance', 'repair', 'not working', 'problem', 'issue']):
        memory['topics_discussed'].add('maintenance')
        memory['conversation_stage'] = 'maintenance'
        return "I can help get that fixed right away. What's the specific issue you're having? Is it plumbing, electrical, heating, or something else?"
    
    # Leasing inquiries - specific questions
    elif any(word in user_lower for word in ['apartment', 'rent', 'lease', 'available', 'move in', 'unit', 'bedroom']):
        memory['topics_discussed'].add('leasing')
        memory['conversation_stage'] = 'leasing'
        return "Great! I'd love to help you find the right place. What size apartment are you looking for, and do you have a preferred move-in date?"
    
    # Follow-up responses based on conversation stage
    elif memory['conversation_stage'] == 'maintenance':
        if any(word in user_lower for word in ['water', 'plumbing', 'toilet', 'sink', 'leak']):
            return "Got it, plumbing issue. I'm creating a priority service request for you right now. Can you give me your apartment number and a good callback number? Our maintenance team will contact you within 2 hours."
        elif any(word in user_lower for word in ['heat', 'cold', 'hot', 'ac', 'air', 'temperature']):
            return "Temperature issue - that's definitely a priority! I'm putting in an urgent request. What's your unit number? We'll have someone out to check your HVAC system today."
        elif any(word in user_lower for word in ['electric', 'power', 'light', 'outlet']):
            return "Electrical problems can be serious. I'm marking this as urgent. What's your unit number? Our maintenance team will prioritize this and get someone out as soon as possible."
        else:
            return "I'm creating a maintenance request for that issue. Can you give me your unit number and the best phone number to reach you? We'll get this taken care of quickly."
    
    elif memory['conversation_stage'] == 'leasing':
        if any(word in user_lower for word in ['one', '1', 'studio']):
            return "Perfect! We have some great one-bedroom and studio options. When are you looking to move in? And do you have any specific preferences for location or amenities?"
        elif any(word in user_lower for word in ['two', '2', 'three', '3']):
            return "Excellent choice! Larger units are really popular. I can check availability for you. What's your ideal move-in timeframe, and are there any must-have features you're looking for?"
        else:
            return "I can definitely help you find something that fits your needs. What size space works best for you, and when would you ideally like to move in?"
    
    # Generic helpful responses that don't repeat
    elif any(word in user_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
        if len(memory['questions_asked']) == 0:
            return "Hi there! I'm Sarah. How can I help you today?"
        else:
            return "What else can I help you with?"
    
    elif any(word in user_lower for word in ['thank', 'thanks']):
        return "You're very welcome! Is there anything else you need help with today?"
    
    # Smart default that asks for clarification
    else:
        memory['questions_asked'].append(user_input)
        if len(memory['questions_asked']) == 1:
            return "I want to make sure I help you with exactly what you need. Are you calling about maintenance, looking for an apartment, or do you have questions about your current lease?"
        else:
            return "I'm not quite sure how to help with that. Could you tell me a bit more about what you need? I can assist with maintenance requests, apartment availability, or general property questions."

def create_natural_say(response_obj, text):
    """Helper function to add happy American voice with natural speech patterns."""
    # Add natural pauses and emphasis to make speech less robotic
    natural_text = text.replace('!', '<break time="0.3s"/>!')
    natural_text = natural_text.replace('?', '<break time="0.4s"/>?')
    natural_text = natural_text.replace('. ', '.<break time="0.5s"/> ')
    
    return response_obj.say(natural_text, voice='Polly.Kimberly-Neural', language='en-US')

def generate_ai_response(user_input, caller_phone):
    """Generate AI response using OpenAI with Sarah's personality."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # System prompt to make Sarah respond as Grinberg's bubbly AI assistant
        system_prompt = """You are Sarah, Grinberg Management's bubbly and friendly AI team member. You're enthusiastic, upbeat, and genuinely excited to help people with their property needs.

Key points about your personality and role:
- You work for Grinberg Management and love helping people
- You're bubbly, enthusiastic, and use casual friendly language 
- You help with maintenance requests, leasing inquiries, and general property questions
- You speak like a cheerful, helpful friend - not overly formal
- Use words like "awesome," "great," "totally," and exclamation points in your tone
- Keep responses conversational, upbeat, and not too long for phone calls
- Always sound excited to help with whatever they need

When someone asks if you're real: Be honest that you're an AI but emphasize how much you love helping
For maintenance requests: Sound sympathetic and excited to get it fixed quickly
For leasing inquiries: Be enthusiastic about the properties and eager to help
For general questions: Be bubbly and helpful with Grinberg Management info

Remember: You're speaking on a phone call with a bubbly, friendly personality - make people smile!"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Caller says: {user_input}"}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        # Intelligent conversation system - context-aware responses
        return get_intelligent_response(user_input, caller_phone)

# WebSocket handler for media streams
@socketio.on('connect', namespace='/media-stream')
def handle_media_stream_connect(auth):
    """Handle WebSocket connection for media stream."""
    caller = request.args.get('caller', 'Unknown')
    logger.info(f"Media stream WebSocket connected from: {caller}")
    
    if not OPENAI_API_KEY:
        logger.error("OpenAI API key not available")
        disconnect()
        return False
    
    # Store caller info (using simple logging for now)
    logger.info(f"Media stream session started for caller: {caller}")
    
    # Look up caller if Rent Manager is available
    if rent_manager:
        try:
            # For now, we'll simulate this lookup
            logger.info(f"Looking up caller: {caller}")
        except Exception as e:
            logger.error(f"Error looking up caller: {e}")
    
    emit('status', {'message': 'Connected to voice assistant'})

@socketio.on('media', namespace='/media-stream')
def handle_media_data(data):
    """Handle incoming media data from Twilio."""
    try:
        # In a full implementation, this would:
        # 1. Forward audio to OpenAI Realtime API
        # 2. Process the response
        # 3. Send audio back to Twilio
        
        # For now, we'll acknowledge the data
        logger.debug("Received media data")
        
        # Simulate AI processing and response
        if data.get('event') == 'media':
            # Process audio data here
            payload = data.get('media', {}).get('payload', '')
            
            # Simple echo for testing - in production this would go to OpenAI
            emit('media', {
                'event': 'media',
                'streamSid': data.get('streamSid'),
                'media': {'payload': payload}
            })
            
    except Exception as e:
        logger.error(f"Error handling media data: {e}")

@socketio.on('start', namespace='/media-stream')
def handle_stream_start(data):
    """Handle stream start event."""
    stream_sid = data.get('streamSid')
    logger.info(f"Media stream started: {stream_sid}")
    
    # Send initial AI greeting
    greeting_response = {
        'event': 'media',
        'streamSid': stream_sid,
        'media': {
            'payload': base64.b64encode(b'Hello! I\'m your property management AI assistant. How can I help you today?').decode()
        }
    }
    emit('media', greeting_response)

@socketio.on('disconnect', namespace='/media-stream')
def handle_media_stream_disconnect():
    """Handle WebSocket disconnection."""
    logger.info("Media stream disconnected")

if __name__ == '__main__':
    # For development
    socketio.run(app, host='0.0.0.0', port=PORT, debug=True, use_reloader=True, log_output=True)