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

@app.route('/webhook-test')
def webhook_test():
    """Test endpoint to verify Twilio webhook connectivity."""
    return jsonify({
        "status": "success",
        "message": "Webhook endpoint is accessible",
        "timestamp": str(__import__('datetime').datetime.now()),
        "app_url": request.host_url,
        "endpoints": {
            "incoming_call": "/incoming-call",
            "process_speech": "/process-speech", 
            "health": "/health"
        },
        "environment": {
            "openai_configured": bool(OPENAI_API_KEY),
            "twilio_configured": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN)
        }
    })

@app.route('/twilio-test', methods=['POST'])
def twilio_test():
    """Minimal test endpoint that mimics Twilio webhook structure."""
    try:
        logger.info(f"Twilio test request: {dict(request.values)}")
        response = VoiceResponse()
        response.say("Hi there! This is Sarah from Grinberg Management! I'm super excited to tell you that our webhook is working perfectly! Isn't that awesome?",
                    voice='Polly.Joanna-Neural', language='en-US')
        return str(response)
    except Exception as e:
        logger.error(f"Twilio test error: {e}")
        return "Error in webhook", 500

@app.route('/incoming-call', methods=['GET', 'POST'])
def handle_incoming_call():
    """Handle incoming call and return TwiML response."""
    try:
        # Get caller information from Twilio
        caller_phone = request.values.get('From', 'Unknown')
        call_sid = request.values.get('CallSid', 'Unknown')
        
        logger.info(f"Incoming call from: {caller_phone}, CallSid: {call_sid}")
        logger.info(f"Twilio request data: {dict(request.values)}")
        
        response = VoiceResponse()
        
        # Check if OpenAI API key is available
        if not OPENAI_API_KEY:
            response.say("Hi there! Thanks so much for calling Grinberg Management! I'm Sarah, but I'm having some technical hiccups right now. I'm super sorry about that! Please leave me a message after the beep and I'll make sure our amazing team gets right back to you!",
                        voice='Polly.Joanna-Neural', language='en-US')
            response.record(timeout=30, transcribe=False)
            return str(response)
        
        # Genuinely happy, enthusiastic greeting with natural emotion
        greeting = "Hi! Oh my gosh, it's such a beautiful day here at Grinberg Management! This is Sarah, and I'm so excited to help you today! What can I do for you?"
        response.say(greeting, voice='Polly.Joanna-Neural', language='en-US')
        
        # Use speech gathering instead of media streaming for better reliability
        gather = response.gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action='/process-speech',
            method='POST'
        )
        
        # Fallback if no speech detected - bubbly and encouraging  
        response.say("Oops! I totally missed that! Could you say it again? I'm all ears!",
                    voice='Polly.Joanna-Neural', language='en-US')
        
        logger.info(f"Returning TwiML response for {caller_phone}")
        return str(response)
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}", exc_info=True)
        response = VoiceResponse()
        response.say("Oh gosh, I'm having some technical trouble right now! I'm so sorry about that! Could you try calling back in just a few minutes? I promise I'll be back to my happy, helpful self!",
                    voice='Polly.Joanna-Neural', language='en-US')
        return str(response)

@app.route('/fallback-call', methods=['POST'])
def fallback_call():
    """Fallback handler in case primary webhook fails."""
    try:
        logger.warning("Fallback handler activated")
        caller_phone = request.values.get('From', 'Unknown')
        logger.info(f"Fallback call from: {caller_phone}")
        
        response = VoiceResponse()
        response.say("Hi! Oh my gosh, it's such a beautiful day here at Grinberg Management! This is Sarah, and I'm so excited to help you today! What can I do for you?",
                    voice='Polly.Joanna-Neural', language='en-US')
        
        response.gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action='/process-speech',
            method='POST'
        )
        
        response.say("Oops! I totally missed that! Could you say it again? I'm all ears!",
                    voice='Polly.Joanna-Neural', language='en-US')
        
        return str(response)
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
            response.say("Oh no, I totally spaced out there! What were you saying?",
                        voice='Polly.Joanna-Neural', language='en-US')
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
            response.say(ai_response, voice='Polly.Joanna-Neural', language='en-US')
        except Exception as ai_error:
            logger.error(f"OpenAI error: {ai_error}")
            # Fallback to intelligent keyword processing using our smart response system
            fallback_response = get_intelligent_response(speech_result, caller_phone)
            response.say(fallback_response, voice='Polly.Joanna-Neural', language='en-US')
        
        # Give option to continue or end call
        response.gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/process-speech',
            method='POST'
        )
        
        response.say("Thanks so much for calling! You have the most amazing day ever, okay? Bye!", voice='Polly.Joanna-Neural', language='en-US')
        
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
    
    # AI/Human identity questions - bubbly, enthusiastic responses
    if any(word in user_lower for word in ['human', 'real person', 'real', 'robot', 'ai', 'computer', 'bot', 'siri']):
        if 'identity' not in memory['topics_discussed']:
            memory['topics_discussed'].add('identity')
            return "Haha, you totally caught me! I'm Sarah and I'm actually an AI, but I'm like, super enthusiastic about helping people! I absolutely love dealing with maintenance stuff, apartment hunting, and basically anything property-related here at Grinberg! So what's up? What can I help you with?"
        else:
            return "Yep, still me - your super cheerful AI buddy Sarah! So what awesome thing can I help you with today?"
    
    # Office hours and availability - smart time-aware responses
    elif any(word in user_lower for word in ['office', 'hours', 'open', 'closed', 'time']):
        import datetime
        now = datetime.datetime.now()
        current_hour = now.hour
        current_day = now.weekday()  # Monday = 0, Sunday = 6
        
        if 'office_hours' not in memory['topics_discussed']:
            memory['topics_discussed'].add('office_hours')
            # Check if it's currently business hours
            if current_day < 5 and 9 <= current_hour < 17:  # Mon-Fri, 9am-5pm
                return "Yes, we're open right now! Our office hours are Monday through Friday, 9 AM to 5 PM. What can I help you with today?"
            elif current_day < 5 and current_hour < 9:
                return "We'll be opening at 9 AM this morning! Our office hours are Monday through Friday, 9 AM to 5 PM. But I'm here now - what can I help you with?"
            elif current_day < 5 and current_hour >= 17:
                return "We're closed for the day, but we'll be back tomorrow at 9 AM! Our office hours are Monday through Friday, 9 AM to 5 PM. I'm still here though - what do you need help with?"
            else:  # Weekend
                return "We're closed for the weekend, but we'll be back Monday at 9 AM! Our office hours are Monday through Friday, 9 AM to 5 PM. I'm available though - what can I help you with?"
        else:
            return "Like I mentioned, we're open 9 to 5, Monday through Friday. What else can I help you with?"

    # Location/office questions with enthusiastic help
    elif any(word in user_lower for word in ['where', 'located', 'address', 'location']):
        if 'location' not in memory['topics_discussed']:
            memory['topics_discussed'].add('location')
            return "Oh awesome question! We have so many amazing properties all over the area! Are you one of our current tenants, or are you looking to find a new place? That'll help me point you in exactly the right direction!"
        else:
            return "Which specific location are you asking about? Our main leasing office or one of our property addresses? I'm excited to help!"
    
    # Maintenance requests - genuinely caring and enthusiastic
    elif any(word in user_lower for word in ['fix', 'broken', 'maintenance', 'repair', 'not working', 'problem', 'issue']):
        memory['topics_discussed'].add('maintenance')
        memory['conversation_stage'] = 'maintenance'
        return "Oh my goodness, something's giving you trouble? I am so sorry about that! But don't you worry one bit - I'm gonna get our absolutely amazing maintenance team on this right away! Tell me what's going on - is it plumbing, electrical, heating, or something else? I want to make sure we get this fixed for you super fast!"
    
    # Leasing inquiries - specific questions
    elif any(word in user_lower for word in ['apartment', 'rent', 'lease', 'available', 'move in', 'unit', 'bedroom']):
        memory['topics_discussed'].add('leasing')
        memory['conversation_stage'] = 'leasing'
        return "Perfect! I can help you find a place. What size apartment do you need, and when do you want to move in?"
    
    # Follow-up responses based on conversation stage
    elif memory['conversation_stage'] == 'maintenance':
        if any(word in user_lower for word in ['water', 'plumbing', 'toilet', 'sink', 'leak']):
            return "Oh my goodness, a plumbing issue! I can totally understand how stressful that must be! Don't worry though - I'm getting our amazing plumbing team on this right away as a priority! What's your apartment number? And what's the best phone number for you? They're gonna call you within just a couple hours and get this all sorted out for you!"
        elif any(word in user_lower for word in ['heat', 'cold', 'hot', 'ac', 'air', 'temperature']):
            return "Oh no, temperature problems are seriously the worst! I feel so bad for you! But hey, don't worry one bit - I'm sending this straight to our incredible HVAC team right now as urgent! What's your unit number? We're gonna have someone out there today to get you all cozy and comfortable again!"
        elif any(word in user_lower for word in ['electric', 'power', 'light', 'outlet']):
            return "Electrical issues can be super scary, so we take those really seriously! I'm marking this as our highest priority right now! What's your unit number? Our fantastic maintenance team is gonna get someone out there super fast to make sure everything's totally safe for you!"
        else:
            return "Perfect! I'm setting up a maintenance request for you right this second! What's your apartment number and the best phone number to reach you? Our awesome team is gonna take care of this so quickly for you!"
    
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
            return "Hi there! I'm Sarah, and I'm absolutely thrilled to help you with whatever you need today! What's going on? I'm super excited to help!"
        else:
            return "What else can I help you with? I'm all ears and ready to help!"
    
    elif any(word in user_lower for word in ['thank', 'thanks']):
        return "Aww, you're so welcome! I'm just happy I could help! Is there anything else you need today? I'm here for you!"
    
    # Payment and rent questions - helpful information
    elif any(word in user_lower for word in ['rent', 'payment', 'pay', 'bill', 'due', 'portal']):
        return "Oh great question about payments! You can totally use our super convenient online portal, or you can call our main office - they're absolutely amazing! Do you need help getting into your account, or is there something specific about payments I can help you with? I'm here to make this as easy as possible for you!"
    
    # Emergency maintenance - prioritize
    elif any(word in user_lower for word in ['emergency', 'urgent', 'flooding', 'no heat', 'no power']):
        return "Oh my gosh, that sounds super urgent! For serious emergencies like flooding, no heat, or power outages, I'm marking this as our absolute highest priority right now! What's your unit number? I'm getting our emergency maintenance team on this immediately - they're incredible and they'll take such good care of you!"
    
    # Property amenities and features
    elif any(word in user_lower for word in ['amenities', 'pool', 'gym', 'parking', 'laundry', 'pet']):
        return "Ooh, I love talking about our amenities! We have so many awesome features! Each property has different amazing things. Are you asking about a specific building, or are you thinking about moving in and want to know all the cool stuff that's available? I'm so excited to tell you about everything!"
    
    # Smart default that asks for clarification
    else:
        memory['questions_asked'].append(user_input)
        if len(memory['questions_asked']) == 1:
            return "I want to make sure I help you with exactly what you need. Are you calling about maintenance, looking for an apartment, or do you have questions about your current lease?"
        else:
            return "I'm not quite sure how to help with that. Could you tell me a bit more about what you need? I can assist with maintenance requests, apartment availability, or general property questions."

def create_natural_say(response_obj, text):
    """Helper function to add genuinely happy, enthusiastic American voice."""
    # Use Joanna-Neural for most bubbly, human-like voice
    return response_obj.say(text, voice='Polly.Joanna-Neural', language='en-US')

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