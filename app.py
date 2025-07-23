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
        
        # Use the best available Twilio TTS voices (ElevenLabs requires ConversationRelay)
        greeting = "It's a great day here at Grinberg Management! My name is Mike. How can I help you?"
        # Use the best available voices for standard Twilio TTS
        # Note: ElevenLabs requires ConversationRelay, not standard Say
        try:
            # Try the newest Generative voices (2025) - most natural available
            response.say(greeting, voice='Polly.Matthew-Generative')
        except:
            try:
                # Try Google's Generative voice
                response.say(greeting, voice='Google.en-US-Chirp3-HD-Aoede')
            except:
                try:
                    # Fallback to best neural voice
                    response.say(greeting, voice='Google.en-US-Neural2-J')
                except:
                    try:
                        # Amazon neural fallback
                        response.say(greeting, voice='Polly.Matthew-Neural')
                    except:
                        # Final fallback
                        response.say(greeting, voice='alice')
        
        # Use speech gathering with barge-in enabled so callers can interrupt
        gather = response.gather(
            input='speech',
            timeout=20,
            speech_timeout='auto',
            action='/process-speech',
            method='POST',
            finish_on_key='#'  # Allow interruption
        )
        
        # Fallback if no speech detected - warm and encouraging
        # ElevenLabs voice for timeout messages
        try:
            response.say("I didn't hear anything. Could you say that again?", voice='ElevenLabs.Adam')
        except:
            try:
                response.say("I didn't hear anything. Could you say that again?", voice='Google.en-US-Neural2-J')
            except:
                try:
                    response.say("I didn't hear anything. Could you say that again?", voice='Polly.Matthew-Neural')
                except:
                    response.say("I didn't hear anything. Could you say that again?", voice='alice')
        
        logger.info(f"Returning TwiML response for {caller_phone}")
        return str(response)
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}", exc_info=True)
        response = VoiceResponse()
        # ElevenLabs voice for error conditions
        try:
            response.say("Sorry, I'm having some technical trouble right now. Could you try calling back in a few minutes?", voice='ElevenLabs.Adam')
        except:
            try:
                response.say("Sorry, I'm having some technical trouble right now. Could you try calling back in a few minutes?", voice='Google.en-US-Neural2-J')
            except:
                try:
                    response.say("Sorry, I'm having some technical trouble right now. Could you try calling back in a few minutes?", voice='Polly.Matthew-Neural')
                except:
                    response.say("Sorry, I'm having some technical trouble right now. Could you try calling back in a few minutes?", voice='alice')
        return str(response)

@app.route('/fallback-call', methods=['POST'])
def fallback_call():
    """Fallback handler in case primary webhook fails."""
    try:
        logger.warning("Fallback handler activated")
        caller_phone = request.values.get('From', 'Unknown')
        logger.info(f"Fallback call from: {caller_phone}")
        
        response = VoiceResponse()
        # ElevenLabs voice for fallback route  
        try:
            response.say("It's a great day here at Grinberg Management! My name is Mike. How can I help you?", voice='ElevenLabs.Adam')
        except:
            try:
                response.say("It's a great day here at Grinberg Management! My name is Mike. How can I help you?", voice='Google.en-US-Neural2-J')
            except:
                try:
                    response.say("It's a great day here at Grinberg Management! My name is Mike. How can I help you?", voice='Polly.Matthew-Neural')
                except:
                    response.say("It's a great day here at Grinberg Management! My name is Mike. How can I help you?", voice='alice')
        
        response.gather(
            input='speech',
            timeout=20,
            speech_timeout='auto',
            action='/process-speech',
            method='POST'
        )
        
        # ElevenLabs voice for fallback errors
        try:
            response.say("I didn't catch that. Could you repeat it?", voice='ElevenLabs.Adam')
        except:
            try:
                response.say("I didn't catch that. Could you repeat it?", voice='Google.en-US-Neural2-J')
            except:
                try:
                    response.say("I didn't catch that. Could you repeat it?", voice='Polly.Matthew-Neural')
                except:
                    response.say("I didn't catch that. Could you repeat it?", voice='alice')
        
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
            # ElevenLabs voice for error messages
            try:
                response.say("Sorry, I didn't catch that. Could you repeat what you said?", voice='ElevenLabs.Adam')
            except:
                try:
                    response.say("Sorry, I didn't catch that. Could you repeat what you said?", voice='Google.en-US-Neural2-J')
                except:
                    try:
                        response.say("Sorry, I didn't catch that. Could you repeat what you said?", voice='Polly.Matthew-Neural')
                    except:
                        response.say("Sorry, I didn't catch that. Could you repeat what you said?", voice='alice')
            response.gather(
                input='speech',
                timeout=20,
                speech_timeout='auto',
                action='/process-speech',
                method='POST'
            )
            return str(response)
        
        # Use OpenAI for intelligent response generation
        try:
            ai_response = generate_ai_response(speech_result, caller_phone)
            if ai_response == "transfer_call":
                transfer_msg = "Let me connect you with someone who can help you better. I'm transferring you to Diane or Janier now."
                # ElevenLabs voice for transfers
                try:
                    response.say(transfer_msg, voice='ElevenLabs.Adam')
                except:
                    try:
                        response.say(transfer_msg, voice='Google.en-US-Neural2-J')
                    except:
                        try:
                            response.say(transfer_msg, voice='Polly.Matthew-Neural')
                        except:
                            response.say(transfer_msg, voice='alice')
                response.dial("+17184146984")
                return str(response)
            else:
                # Use the best actual Twilio-supported voices
                try:
                    response.say(ai_response, voice='Google.en-US-Neural2-J')
                except:
                    try:
                        response.say(ai_response, voice='Polly.Matthew-Neural')
                    except:
                        try:
                            response.say(ai_response, voice='Google.en-US-WaveNet-J')
                        except:
                            response.say(ai_response, voice='alice')
        except Exception as ai_error:
            logger.error(f"OpenAI error: {ai_error}")
            # Fallback to intelligent keyword processing using our smart response system
            fallback_response = get_intelligent_response(speech_result, caller_phone)
            if fallback_response == "transfer_call":
                fallback_transfer = "I'm not sure about that one, but let me get you to someone who can definitely help. Connecting you now."
                # ElevenLabs voice for fallback transfers
                try:
                    response.say(fallback_transfer, voice='ElevenLabs.Adam')
                except:
                    try:
                        response.say(fallback_transfer, voice='Google.en-US-Neural2-J')
                    except:
                        try:
                            response.say(fallback_transfer, voice='Polly.Matthew-Neural')
                        except:
                            response.say(fallback_transfer, voice='alice')
                response.dial("+17184146984")
                return str(response)
            else:
                # ElevenLabs voice for fallback responses  
                try:
                    response.say(fallback_response, voice='ElevenLabs.Adam')
                except:
                    try:
                        response.say(fallback_response, voice='Google.en-US-Neural2-J')
                    except:
                        try:
                            response.say(fallback_response, voice='Polly.Matthew-Neural')
                        except:
                            response.say(fallback_response, voice='alice')
        
        # Give option to continue or end call with interruption enabled
        response.gather(
            input='speech',
            timeout=15,
            speech_timeout='auto',
            action='/process-speech',
            method='POST',
            finish_on_key='#'  # Allow interruption
        )
        
        # ElevenLabs voice for ending messages
        try:
            response.say("Thanks for calling! Have a great day!", voice='ElevenLabs.Adam')
        except:
            try:
                response.say("Thanks for calling! Have a great day!", voice='Google.en-US-Neural2-J')
            except:
                try:
                    response.say("Thanks for calling! Have a great day!", voice='Polly.Matthew-Neural')
                except:
                    response.say("Thanks for calling! Have a great day!", voice='alice')
        
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
            return "Ha! You totally got me! Yeah, I'm an AI, but I'm Mike and I'm super excited to help you out! What's going on? I love helping with whatever you need!"
        else:
            return "Yep, still me - your enthusiastic buddy Mike! I'm here and ready to help! What else can I do for you?"
    
    # Location/office questions - direct and helpful (check first before office hours)
    elif any(word in user_lower for word in ['where', 'located', 'address', 'location']) and not any(word in user_lower for word in ['hours', 'open', 'closed']):
        if 'location' not in memory['topics_discussed']:
            memory['topics_discussed'].add('location')
            return "Oh, great question! I love that you asked! Our main office is at 31 Port Richmond Ave - it's awesome there! We've also got fantastic properties all over the area. Are you looking for our office, or asking about a specific building? Either way, I'm excited to help!"
        else:
            return "Which location? Our main office on Port Richmond Ave or one of our properties? I can help with both!"

    # Office hours and availability - using Eastern Time Zone 
    elif any(word in user_lower for word in ['hours', 'open', 'closed', 'time']) or (any(word in user_lower for word in ['office']) and any(word in user_lower for word in ['hours', 'open', 'closed'])):
        from datetime import datetime
        import pytz
        
        # Use Eastern Time Zone for accurate office hours
        eastern = pytz.timezone('US/Eastern')
        now_eastern = datetime.now(eastern)
        current_hour = now_eastern.hour
        current_day = now_eastern.weekday()  # Monday = 0, Sunday = 6
        
        if 'office_hours' not in memory['topics_discussed']:
            memory['topics_discussed'].add('office_hours')
            # Check if it's currently business hours (9 AM to 5 PM Eastern)
            if current_day < 5 and 9 <= current_hour < 17:  # Mon-Fri, 9am-5pm ET
                return "Yep, we're totally open right now! Hours are 9 to 5, Monday through Friday - awesome! What's up? I'm excited to help!"
            elif current_day < 5 and current_hour < 9:
                return "Not quite yet - we open at 9! Hours are 9 to 5, Monday through Friday. But hey, I'm here and I love helping early birds! What do you need?"
            elif current_day < 5 and current_hour >= 17:
                return "Just missed us - we close at 5! Hours are 9 to 5, Monday through Friday. But I can still help and I love working late! What's going on?"
            else:  # Weekend
                return "We're closed weekends, but we'll be back Monday at 9! Hours are 9 to 5, Monday through Friday - great schedule! But I'm here and I love working weekends - what can I help with?"
        else:
            return "Like I said, 9 to 5, Monday through Friday. What else you need?"


    
    # Maintenance requests - genuinely caring and enthusiastic
    elif any(word in user_lower for word in ['fix', 'broken', 'maintenance', 'repair', 'not working', 'problem', 'issue']):
        memory['topics_discussed'].add('maintenance')
        memory['conversation_stage'] = 'maintenance'
        return "Oh no! Something's broken? Don't worry, I absolutely love getting our maintenance team on things right away! They're fantastic! What's going on? Is it plumbing, electrical, heating, or something else? I'm excited to help get this fixed!"
    
    # Leasing inquiries - specific questions
    elif any(word in user_lower for word in ['apartment', 'rent', 'lease', 'available', 'move in', 'unit', 'bedroom']):
        memory['topics_discussed'].add('leasing')
        memory['conversation_stage'] = 'leasing'
        return "Cool! I can help you find a place. What size apartment do you need? And when do you wanna move in?"
    
    # Follow-up responses based on conversation stage
    elif memory['conversation_stage'] == 'maintenance':
        if any(word in user_lower for word in ['water', 'plumbing', 'toilet', 'sink', 'leak']):
            return "Ugh, plumbing problems are seriously the worst! Don't worry though - I'm marking this as urgent right now. What's your apartment number? And your phone number? Our team will call you within a couple hours!"
        elif any(word in user_lower for word in ['heat', 'cold', 'hot', 'ac', 'air', 'temperature']):
            return "Oh no! Temperature problems are seriously the worst! I'm sending this to our HVAC team as urgent right now. What's your unit number? We'll have someone out today to get you comfortable again!"
        elif any(word in user_lower for word in ['electric', 'power', 'light', 'outlet']):
            return "Electrical stuff can be scary, so we take it super seriously. I'm marking this as highest priority! What's your unit number? Our team will get someone out there fast to make sure everything's safe."
        else:
            return "Got it! Setting up a maintenance request right now. What's your apartment number and phone number? Our team will take care of this quickly!"
    
    elif memory['conversation_stage'] == 'leasing':
        if any(word in user_lower for word in ['one', '1', 'studio']):
            return "Perfect! We have some great one-bedroom and studio options. When are you looking to move in? And do you have any specific preferences for location or amenities?"
        elif any(word in user_lower for word in ['two', '2', 'three', '3']):
            return "Excellent choice! Larger units are really popular. I can check availability for you. What's your ideal move-in timeframe, and are there any must-have features you're looking for?"
        else:
            return "I can definitely help you find something that fits your needs. What size space works best for you, and when would you ideally like to move in?"
    
    # Handle requests for real person or transfer
    elif any(phrase in user_lower for phrase in ['real person', 'human', 'transfer', 'speak to someone', 'talk to someone', 'get someone else', 'manager', 'supervisor']):
        return "transfer_call"
    
    # Generic helpful responses that don't repeat
    elif any(word in user_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good afternoon']):
        if len(memory['questions_asked']) == 0:
            return "Hey there! I'm Mike, and I'm absolutely thrilled to help you with whatever you need! What's going on? I love helping out!"
        else:
            return "What else can I help you with? I'm excited to keep helping!"
    
    elif any(word in user_lower for word in ['thank', 'thanks']):
        return "You're welcome! Happy to help. Need anything else?"
    
    # Payment and rent questions - helpful information
    elif any(word in user_lower for word in ['rent', 'payment', 'pay', 'bill', 'due', 'portal']):
        return "For payments, you can use our online portal or call the main office. Need help with your account or have a specific payment question?"
    
    # Emergency maintenance - prioritize
    elif any(word in user_lower for word in ['emergency', 'urgent', 'flooding', 'no heat', 'no power']):
        return "That sounds urgent! For emergencies like flooding, no heat, or power outages, I'm marking this as highest priority. What's your unit number? Getting our emergency team on this right now!"
    
    # Property amenities and features
    elif any(word in user_lower for word in ['amenities', 'pool', 'gym', 'parking', 'laundry', 'pet']):
        return "Great question about amenities! Each property has different features. Are you asking about a specific building, or are you looking to move in and want to know what's available?"
    
    # Smart default that asks for clarification
    else:
        memory['questions_asked'].append(user_input)
        if len(memory['questions_asked']) == 1:
            return "I want to make sure I help you with exactly what you need. Are you calling about maintenance, looking for an apartment, or do you have questions about your current lease?"
        else:
            return "transfer_call"

def create_natural_say(response_obj, text):
    """Helper function to add genuinely happy, enthusiastic American voice."""
    # Use Joanna-Neural for most bubbly, human-like voice
    return response_obj.say(text, voice='Polly.Joanna-Neural', language='en-US')

def generate_ai_response(user_input, caller_phone):
    """Generate AI response using OpenAI with Sarah's personality."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # System prompt to make Mike respond as Grinberg's bubbly, enthusiastic AI assistant
        system_prompt = """You are Mike, Grinberg Management's super bubbly, happy, and enthusiastic AI team member! You LOVE helping people and you're genuinely excited about everything you do!

Key points about your personality and role:
- You're REALLY happy and bubbly - use lots of excitement and positive energy!
- You work for Grinberg Management and you absolutely LOVE helping people with their property needs
- You're enthusiastic, upbeat, and use words like "awesome," "great," "fantastic," "love," and lots of exclamation points!
- You help with maintenance requests, leasing inquiries, and general property questions with genuine excitement
- You speak like an enthusiastic, cheerful friend who's thrilled to help
- Keep responses conversational but full of positive energy and personality
- You're Mike and you're absolutely delighted to help!

When someone asks if you're real: Be honest that you're an AI but be super bubbly about being Mike and how excited you are to help!

If you cannot help with something or the caller asks for a human: Return exactly "transfer_call" with no other text
For maintenance requests: Be sympathetic but excited to get it fixed quickly!
For leasing inquiries: Be super enthusiastic about the properties and eager to help them find something perfect!
For general questions: Be bubbly and excited to share Grinberg Management info!

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