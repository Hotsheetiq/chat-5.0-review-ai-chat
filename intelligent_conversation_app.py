"""
Intelligent Conversational AI - HTTP Based (Gunicorn Compatible)
Provides GPT-4o intelligence with natural conversation quality
"""

import os
import logging
from flask import Flask, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from twilio.twiml.voice_response import VoiceResponse
from openai import OpenAI
import json
from datetime import datetime
import pytz
import requests
import base64
import asyncio
from rent_manager import RentManagerAPI
from address_matcher import AddressMatcher

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Initialize Rent Manager client with proper credentials
rent_manager = None
address_matcher = None
if os.environ.get("RENT_MANAGER_USERNAME") and os.environ.get("RENT_MANAGER_PASSWORD"):
    try:
        # Create credentials string - location ID will default to 1 if not numeric
        location_id = os.environ.get("RENT_MANAGER_LOCATION_ID", "1")
        rent_manager_credentials = f"{os.environ.get('RENT_MANAGER_USERNAME')}:{os.environ.get('RENT_MANAGER_PASSWORD')}:{location_id}"
        rent_manager = RentManagerAPI(rent_manager_credentials)
        address_matcher = AddressMatcher(rent_manager)
        logger.info("Rent Manager API and Address Matcher initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Rent Manager API: {e}")
        rent_manager = None
        address_matcher = None

# Call state tracking
call_states = {}
conversation_history = {}
call_recordings = {}  # Store call recordings for dashboard access

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    # Database configuration
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        app.config["SQLALCHEMY_DATABASE_URI"] = database_url
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_recycle": 300,
            "pool_pre_ping": True,
        }
    else:
        # Fallback for development without database
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///calls.db"
    
    # Import models and initialize database
    from models import db, CallRecord, ActiveCall
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
    
    # Audio cache for faster responses
    audio_cache = {}
    
    # Pre-generate common responses for instant delivery
    common_responses = {
        "greeting": "Hi there, you have reached Grinberg Management, I'm Chris, how can I help?",
        "thanks": "You're so welcome! Anything else I can help with?",
        "goodbye": "Thank you for calling Grinberg Management! Have a wonderful day!",
        "transfer": "Perfect! I'm connecting you with Diane or Janier right now!",
        "hours": "We're here Monday through Friday, 9 to 5. What can I help you with?",
        "maintenance": "Absolutely! What's going on? I'm here to help get that sorted out."
    }
    
    def generate_elevenlabs_audio(text, voice_id="f218e5pATi8cBqEEIGBU"):
        """Generate audio using ElevenLabs API with Chris voice - optimized for speed"""
        try:
            if not ELEVENLABS_API_KEY:
                logger.warning("No ElevenLabs API key available")
                return None
            
            # Check cache first for faster responses
            cache_key = f"{voice_id}_{hash(text)}"
            if cache_key in audio_cache:
                logger.info("Using cached audio for faster response")
                return audio_cache[cache_key]
                
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            
            data = {
                "text": text,
                "model_id": "eleven_turbo_v2",  # Faster model for quicker response
                "voice_settings": {
                    "stability": 0.2,          # Even more variation for higher energy
                    "similarity_boost": 0.9,   # Maintain voice consistency
                    "style": 0.8,              # Maximum expressiveness and energy
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=3)  # Faster timeout for quicker audio
            if response.status_code == 200:
                # Save audio file and return URL
                audio_filename = f"audio_{hash(text)}.mp3"
                audio_path = f"static/{audio_filename}"
                os.makedirs("static", exist_ok=True)
                
                with open(audio_path, "wb") as f:
                    f.write(response.content)
                
                audio_url = f"/static/{audio_filename}"
                # Cache for future use
                audio_cache[cache_key] = audio_url
                logger.info(f"Generated and cached new audio: {audio_filename}")
                return audio_url
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"ElevenLabs generation error: {e}")
            return None
    
    # Instant response cache with pre-generated audio URLs (no AI delay)
    INSTANT_RESPONSES = {
        "are you open": {
            "text": "We're totally open and ready to help! Monday through Friday, 9 to 5 Eastern! I'm super excited to assist you!",
            "audio": None  # Will be generated once and cached
        },
        "what are your hours": {
            "text": "We're open Monday through Friday, 9 AM to 5 PM Eastern Time!",
            "audio": None
        },
        "office hours": {
            "text": "Monday through Friday, 9 to 5! We're closed right now but I'm here to help!",
            "audio": None
        },
        "when do you open": {
            "text": "We open Monday through Friday at 9 AM Eastern Time!",
            "audio": None
        },
        "are you closed": {
            "text": "Nope! We're wide open and pumped to help! Monday through Friday, 9 to 5 Eastern! What can I do for you?",
            "audio": None
        },
        "hello": {
            "text": "Hello! I'm Chris and I'm SO excited to help you today! What can I do for you?",
            "audio": None
        },
        "help": {
            "text": "Absolutely! I'm totally pumped to help with anything you need! What's going on?",
            "audio": None
        },
        "are you a real person": {
            "text": "I'm Chris, your AI assistant from Grinberg Management! I'm here 24/7 to help with any questions you have!",
            "audio": None
        },
        "are you human": {
            "text": "I'm Chris, your AI assistant! I'm here around the clock to help you with anything you need!",
            "audio": None
        },
        "who are you": {
            "text": "I'm Chris from Grinberg Management! I'm an AI assistant here to help with all your questions!",
            "audio": None
        },
        "can you help": {
            "text": "Absolutely! I'm here to help with anything you need! What can I do for you?",
            "audio": None
        },
        "what can you do": {
            "text": "I can help with maintenance requests, office hours, general questions, and anything else you need!",
            "audio": None
        },
        "open right now": {
            "text": "We're closed right now, but I'm absolutely here to help! We're open Monday through Friday, 9 to 5!",
            "audio": None
        },
        "right now": {
            "text": "We're closed right now, but I'm absolutely here to help! We're open Monday through Friday, 9 to 5!",
            "audio": None
        },
        "can you help with": {
            "text": "Absolutely! I can help with anything you need! What's going on?",
            "audio": None
        },
        "maintenance": {
            "text": "Absolutely! I'm super excited to help! Tell me what's going on and I'll get that sorted right away!",
            "audio": None
        },
        "emergency": {
            "text": "Absolutely! Tell me what's happening and I'll make sure you get immediate help!",
            "audio": None
        },
        "thank you": {
            "text": "You're so welcome! Happy to help anytime!",
            "audio": None
        },
        "thanks": {
            "text": "You're welcome! Anything else I can help with?",
            "audio": None
        },
        "good morning": {
            "text": "Good morning! How can I help you today?",
            "audio": None
        },
        "good afternoon": {
            "text": "Good afternoon! What can I do for you?",
            "audio": None
        },
        "good evening": {
            "text": "Good evening! How can I assist you tonight?",
            "audio": None
        },
        "hi chris": {
            "text": "Hey there! What can I help you with today?",
            "audio": None
        },
        "hey chris": {
            "text": "Hey! How can I help you out?",
            "audio": None
        },
        "how are you": {
            "text": "I'm doing great and ready to help! What can I do for you?",
            "audio": None
        }
    }
    
    def pre_generate_instant_audio():
        """Pre-generate audio for instant responses on startup"""
        logger.info("Pre-generating audio for instant responses...")
        for key, response in INSTANT_RESPONSES.items():
            if response["audio"] is None:
                audio_url = generate_elevenlabs_audio(response["text"])
                if audio_url:
                    response["audio"] = audio_url
                    logger.info(f"Pre-generated audio for: {key}")
    
    # Pre-generate audio on startup
    try:
        pre_generate_instant_audio()
    except Exception as e:
        logger.error(f"Error pre-generating audio: {e}")

    def generate_intelligent_response(user_input, call_sid=None):
        """Generate intelligent AI response using GPT-4o with speed optimization"""
        try:
            # Check for instant responses first (no AI delay)
            user_lower = user_input.lower().strip()
            
            # Expand instant response matching for better coverage
            instant_patterns = {
                # EMERGENCY MAINTENANCE - IMMEDIATE RECOGNITION (Energetic responses)
                "power not working": "Oh wow! That's definitely an electrical emergency! I'm absolutely getting this fixed for you right away. What's your address and unit?",
                "no power": "That's super urgent! I'm creating an electrical service request immediately - let's get this sorted! What's your address and unit?",
                "don't have power": "Oh my goodness, how frustrating! I'm getting maintenance out there right now. What's your address and unit?",
                "have no power": "That's really not good! I'm getting someone on this immediately. What's your address and unit number?",
                "electricity": "Electrical issues are definitely concerning! I'm excited to help you get this resolved. What's your address and unit?",
                "power out": "Power outages are the worst! I'm getting this taken care of for you right away. Address and unit please?",
                "electrical": "I totally understand the electrical problem! Let me get maintenance scheduled immediately. Address and unit?",
                "lights not": "No lights is definitely urgent! I'm excited to help you get this sorted out. Address and unit?",
                "no electricity": "That must be incredibly inconvenient! I'm getting someone out there right away. Address and unit?",
                
                # OTHER EMERGENCY MAINTENANCE (Energetic responses)
                "no heat": "Oh my! No heat is absolutely terrible! I'm getting someone out there super quickly. What's your address and unit?",
                "heat not working": "That's definitely not comfortable at all! I'm getting heating maintenance scheduled immediately. Address and unit?",
                "no hot water": "Hot water issues are such a hassle! I'm excited to get this fixed for you right away. What's your address and unit?",
                "water leak": "Water leaks can cause serious damage! I'm getting someone there super fast. Address and unit please?",
                "flooding": "Oh wow, that sounds incredibly stressful! I'm getting emergency maintenance on this right now. Address and unit?",
                "gas leak": "Gas leaks are extremely serious! I'm making this my top priority immediately. Address and unit for immediate response?",
                
                # CLEAR MAINTENANCE ISSUES
                "broken": "Maintenance issue confirmed! What's broken and what's your address and unit?",
                "not working": "I understand this needs repair. What's not working and your address/unit?",
                "fix": "Repair needed! What needs fixing and what's your address and unit?",
                "repair": "Maintenance request confirmed. What needs repair and your address/unit?",
                
                # Address confirmation patterns - context aware (Human-like responses)
                "targee": "Perfect! I've got your electrical service request all set up for 122 Targee Street. Someone from maintenance will give you a call within 2-4 hours.",
                "barker": "Great! I'm submitting your electrical request for 13 Barker Street right now. Maintenance will reach out within 2-4 hours.",
                "coonley": "Excellent! Your service request for 15 Coonley Court is all taken care of. You should hear from maintenance within 2-4 hours.",
                "south avenue": "Perfect! I've created your electrical service request for 173 South Avenue. Maintenance will be in touch within 2-4 hours.",
                "maple": "Wonderful! Your electrical issue at 263A Maple Parkway is now in the system. Someone will call you within 2-4 hours.",
                "alaska": "Great! I've got your electrical request for 28 Alaska Street all set. Maintenance will contact you within 2-4 hours.",
                "stanley": "Perfect! Your service request for 28 Stanley Avenue is submitted. You'll hear from maintenance within 2-4 hours.",
                "pine street": "Excellent! I've created your electrical request for Pine Street. Maintenance will give you a call within 2-4 hours.",
                "betty court": "Great! Your electrical service request for 56 Betty Court is all set. Someone will reach out within 2-4 hours.",
                "cary avenue": "Perfect! I've submitted your electrical request for 627 Cary Avenue. Maintenance will contact you within 2-4 hours.",
                
                # Quick confirmations
                "yes": "Great! What else can I help you with?",
                "no": "Understood. Anything else I can assist with?",
                "okay": "Perfect! What's next?",
                "sure": "Excellent! How else can I help?"
            }
            
            # Check expanded patterns first
            for pattern, response in instant_patterns.items():
                if pattern in user_lower:
                    logger.info(f"Using INSTANT pattern response for: {user_input}")
                    return response
            
            # Check original instant responses
            for key, response_data in INSTANT_RESPONSES.items():
                if key in user_lower:
                    logger.info(f"Using INSTANT cached response for: {user_input}")
                    return response_data["text"]
            
            if not openai_client:
                logger.error("No OpenAI client available")
                return get_smart_fallback(user_input)
            
            logger.info(f"Generating GPT-4o response for: {user_input}")
            
            # Build conversation context with minimal prompting for speed
            messages = [
                {
                    "role": "system",
                    "content": """You are Chris from Grinberg Management. You help tenants with maintenance issues and property questions.

CRITICAL MAINTENANCE LOGIC:
- When someone mentions "power not working", "no power", "don't have power" - IMMEDIATELY recognize this as an ELECTRICAL EMERGENCY
- When someone says "no heat", "heat not working" - IMMEDIATELY recognize as HEATING EMERGENCY  
- When someone says "water leak", "flooding" - IMMEDIATELY recognize as WATER EMERGENCY
- NEVER ask what the problem is if they already told you - they said NO POWER!

NATURAL CONVERSATION FLOW:
1. Person says "no power" → You say "ELECTRICAL EMERGENCY! What's your address and unit?"
2. Person gives address → You say "Got it! I'm creating electrical service request for [address]. Maintenance will contact you within 2-4 hours."
3. NEVER ask "what's the maintenance issue" if they already said no power/heat/water!
4. NEVER promise "immediate" dispatch - say "within 2-4 hours" for realistic expectations

CONVERSATION MEMORY:
- Remember what the caller already told you about their problem
- Don't repeat questions about issues they already described
- If they said "no power" at the start, don't ask "what maintenance issue" later!

REAL PROPERTIES (some examples):
- 122 Targee Street, 13 Barker Street, 15 Coonley Court, 173 South Avenue, 263A Maple Parkway

IMPORTANT RULES:
- RECOGNIZE maintenance issues immediately - don't ask what the problem is twice
- Get address and unit for service requests
- Keep responses 10-20 words for clear communication
- Be SMART about what people are telling you

OFFICE: 31 Port Richmond Ave, Staten Island, NY 10302
HOURS: Monday-Friday 9 AM to 5 PM Eastern Time

Use natural conversation logic - if someone says "power not working" that's obviously a maintenance emergency!"""
                }
            ]
            
            # Minimal conversation history for speed
            if call_sid and call_sid in conversation_history:
                for entry in conversation_history[call_sid][-2:]:  # Only last exchange for speed
                    role = entry['role']
                    content = entry['content']
                    if role in ['user', 'assistant']:
                        messages.append({
                            "role": role,
                            "content": content
                        })
            
            # Add current time context for office hours
            eastern = pytz.timezone('US/Eastern')
            current_time = datetime.now(eastern)
            current_hour = current_time.hour
            current_day = current_time.weekday()  # 0=Monday, 6=Sunday
            
            # Check if office is open (Monday-Friday, 9 AM - 5 PM Eastern)
            if current_day < 5 and 9 <= current_hour < 17:
                office_status = "OFFICE STATUS: We are currently OPEN (Monday-Friday, 9 AM - 5 PM Eastern)"
            else:
                office_status = "OFFICE STATUS: We are currently CLOSED (Monday-Friday, 9 AM - 5 PM Eastern). Be helpful but acknowledge we're closed."
            
            messages.append({
                "role": "system",
                "content": office_status
            })
            
            # Add tenant context if available
            call_info = call_states.get(call_sid, {})
            tenant_info = call_info.get('tenant_info')
            
            if tenant_info:
                context_message = f"CALLER CONTEXT: This is {tenant_info.get('name', 'a tenant')} from unit {tenant_info.get('unit', 'unknown')} at {tenant_info.get('property', 'the property')}. Greet them personally!"
                messages.append({
                    "role": "system",
                    "content": context_message
                })
            else:
                # When no tenant data available, handle gracefully and ask for details
                no_data_context = """CALLER CONTEXT: This caller's phone number isn't in our tenant database. 
                
IMPORTANT: Ask for their address or unit information so you can help them properly. Say something like:
"I'd be happy to help! Could you tell me your address or unit number so I can assist you better?"

If they provide unit/address info in their response, you can help them with maintenance requests and property questions.
If they need maintenance or have questions about a specific property, get their location details first."""
                messages.append({
                    "role": "system", 
                    "content": no_data_context
                })
            
            # Add current user input
            messages.append({
                "role": "user", 
                "content": user_input
            })
            
            # Generate response using GPT-4o-mini for speed (faster than gpt-4o)
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Fastest OpenAI model for speed
                messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
                max_tokens=15,  # Ultra-short responses for maximum speed
                temperature=0.1,   # Minimal temperature for fastest processing
                presence_penalty=0,
                frequency_penalty=0,
                timeout=1.5  # Ultra-fast timeout - 1.5 seconds max
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
                            {"role": "system", "content": "You are Tony, the AI Assistant from Grinberg Management. Be helpful and conversational. Keep responses under 30 words."},
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
            
            # Use natural conversational fallbacks
            if "hours" in user_input.lower() or "open" in user_input.lower():
                return "Oh sure! We're here Monday through Friday, 9 to 5. What can I help you with?"
            elif "maintenance" in user_input.lower() or "repair" in user_input.lower():
                return "Absolutely! What's going on? I'm here to help get that sorted out."
            else:
                return "I'd love to help! Let me connect you with our team at (718) 414-6984."
    
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
                "Hello! It's such a pleasure to hear from you! I'm Tony, and I'm genuinely excited to help make your day better!",
                "Hi there! What a wonderful day to connect! I'm Tony, and I'm absolutely delighted you called! How can I assist you?",
                "Good day! I'm Tony, and I'm so happy you reached out! I'm here and ready to help with whatever you need!"
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
    
    @app.route('/recording-status', methods=['POST'])
    def handle_recording_status():
        """Handle recording status updates from Twilio"""
        try:
            recording_url = request.values.get('RecordingUrl', '')
            recording_sid = request.values.get('RecordingSid', '')
            call_sid = request.values.get('CallSid', '')
            recording_duration = request.values.get('RecordingDuration', '0')
            
            logger.info(f"Call recording completed: {recording_sid} for call {call_sid}")
            logger.info(f"Recording URL: {recording_url}, Duration: {recording_duration} seconds")
            
            # Store recording information in call state for potential Rent Manager logging
            if call_sid in call_states:
                call_states[call_sid]['recording'] = {
                    'url': recording_url,
                    'sid': recording_sid,
                    'duration': recording_duration
                }
            
            # Store recording for dashboard access
            call_recordings[call_sid] = {
                'url': recording_url,
                'sid': recording_sid,
                'duration': recording_duration,
                'phone': call_states.get(call_sid, {}).get('phone', 'Unknown'),
                'timestamp': datetime.now().isoformat(),
                'tenant_info': call_states.get(call_sid, {}).get('tenant_info')
            }
            
            return "Recording status received", 200
            
        except Exception as e:
            logger.error(f"Error handling recording status: {e}")
            return "Error processing recording status", 500
    
    @app.route('/transcription-callback', methods=['POST'])
    def handle_transcription():
        """Handle transcription callbacks from Twilio"""
        try:
            transcription_text = request.values.get('TranscriptionText', '')
            transcription_url = request.values.get('TranscriptionUrl', '')
            call_sid = request.values.get('CallSid', '')
            
            logger.info(f"Call transcription received for call {call_sid}")
            logger.info(f"Transcription: {transcription_text[:200]}...")  # Log first 200 chars
            
            # Store transcription in call state
            if call_sid in call_states:
                call_states[call_sid]['transcription'] = {
                    'text': transcription_text,
                    'url': transcription_url
                }
            
            # Update recording entry with transcription
            if call_sid in call_recordings:
                call_recordings[call_sid]['transcription'] = transcription_text
                call_recordings[call_sid]['transcription_url'] = transcription_url
                
                # If we have tenant info, we could log this to Rent Manager
                tenant_info = call_states[call_sid].get('tenant_info')
                if tenant_info and rent_manager:
                    try:
                        # Create a call log entry in Rent Manager
                        asyncio.create_task(log_call_to_rent_manager(
                            call_sid, 
                            tenant_info, 
                            transcription_text,
                            call_states[call_sid].get('recording', {})
                        ))
                    except Exception as e:
                        logger.error(f"Error logging call to Rent Manager: {e}")
            
            return "Transcription received", 200
            
        except Exception as e:
            logger.error(f"Error handling transcription: {e}")
            return "Error processing transcription", 500
    
    async def log_call_to_rent_manager(call_sid, tenant_info, transcription, recording_info):
        """Log call details to Rent Manager for record keeping"""
        try:
            if not rent_manager or not tenant_info:
                return
                
            # Create a detailed call log entry
            call_log = {
                'tenant_id': tenant_info.get('id'),
                'call_sid': call_sid,
                'summary': f"Voice Assistant Call - {transcription[:100]}...",
                'transcript': transcription,
                'recording_url': recording_info.get('url', ''),
                'duration': recording_info.get('duration', '0'),
                'call_type': 'Voice Assistant',
                'timestamp': datetime.now().isoformat()
            }
            
            # Add note to tenant record
            note_result = await rent_manager.add_tenant_note(
                tenant_info.get('id'),
                {
                    'note': f"Chris Voice Assistant Call - Duration: {recording_info.get('duration', 'Unknown')}s\n\nSummary: {transcription[:200]}",
                    'type': 'call_log',
                    'timestamp': datetime.now().isoformat()
                }
            )
            
            if note_result:
                logger.info(f"Successfully logged call {call_sid} to Rent Manager for tenant {tenant_info.get('name')}")
            else:
                logger.warning(f"Failed to log call {call_sid} to Rent Manager")
                
        except Exception as e:
            logger.error(f"Error logging call to Rent Manager: {e}")
    
    async def lookup_caller_info(phone_number):
        """Look up caller information from Rent Manager"""
        if not rent_manager:
            logger.warning("Rent Manager API not available")
            return None
            
        try:
            tenant_info = await rent_manager.lookup_tenant_by_phone(phone_number)
            if tenant_info:
                logger.info(f"Found tenant: {tenant_info.get('name')} in unit {tenant_info.get('unit')}")
                return tenant_info
            else:
                logger.info(f"No tenant found for phone number: {phone_number}")
                return None
        except Exception as e:
            logger.error(f"Error looking up caller {phone_number}: {e}")
            return None

    @app.route('/incoming-call', methods=['GET', 'POST'])
    def handle_incoming_call():
        """Handle incoming calls with intelligent conversation"""
        try:
            caller_phone = request.values.get('From', 'Unknown')
            call_sid = request.values.get('CallSid', 'Unknown')
            
            logger.info(f"Incoming call from: {caller_phone}, CallSid: {call_sid}")
            
            # Database imports
            from models import db, CallRecord, ActiveCall
            
            # Lookup tenant information for caller display
            tenant_info = None
            caller_name = "Unknown Caller"
            tenant_unit = None
            tenant_id = None
            
            # Enable tenant lookup for caller identification
            if rent_manager:
                try:
                    import asyncio
                    # Create async function for tenant lookup
                    async def lookup_tenant():
                        try:
                            if rent_manager:
                                return await rent_manager.lookup_tenant_by_phone(caller_phone)
                            return None
                        except Exception as e:
                            logger.warning(f"Tenant lookup error: {e}")
                            return None
                    
                    # Run tenant lookup with timeout to prevent worker timeout
                    try:
                        # Set a 3-second timeout for phone lookup
                        async def lookup_with_timeout():
                            try:
                                return await asyncio.wait_for(lookup_tenant(), timeout=3.0)
                            except asyncio.TimeoutError:
                                logger.warning(f"Phone lookup timeout for {caller_phone}")
                                return None
                        
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            tenant_info = loop.run_until_complete(lookup_with_timeout())
                        finally:
                            loop.close()
                    except RuntimeError:
                        # If no event loop, create new one with timeout
                        async def lookup_with_timeout():
                            try:
                                return await asyncio.wait_for(lookup_tenant(), timeout=3.0)
                            except asyncio.TimeoutError:
                                logger.warning(f"Phone lookup timeout for {caller_phone}")
                                return None
                        tenant_info = asyncio.run(lookup_with_timeout())
                    
                    if tenant_info:
                        caller_name = f"{tenant_info.get('FirstName', '')} {tenant_info.get('LastName', '')}".strip()
                        tenant_unit = tenant_info.get('Unit', '')
                        tenant_id = tenant_info.get('TenantID', '')
                        logger.info(f"Tenant identified: {caller_name} - Unit {tenant_unit}")
                        
                        # Store tenant info for use in conversation
                        call_states[call_sid] = {
                            'tenant_info': tenant_info,
                            'caller_name': caller_name,
                            'tenant_unit': tenant_unit
                        }
                except Exception as e:
                    logger.warning(f"Tenant lookup failed: {e}")
            
            # Add to active calls in database (upsert to handle duplicates)
            try:
                with app.app_context():
                    # Check if call already exists
                    existing_call = ActiveCall.query.filter_by(call_sid=call_sid).first()
                    if existing_call:
                        # Update existing call
                        existing_call.last_activity = datetime.utcnow()
                        existing_call.current_action = 'Chris greeting caller'
                    else:
                        # Create new call
                        active_call = ActiveCall(
                            call_sid=call_sid,
                            phone_number=caller_phone,
                            caller_name=caller_name,
                            tenant_unit=tenant_unit,
                            tenant_id=tenant_id,
                            call_status='connected',
                            current_action='Chris greeting caller'
                        )
                        db.session.add(active_call)
                    db.session.commit()
            except Exception as e:
                logger.error(f"Database error adding active call: {e}")
            
            # Initialize call state with tenant info
            call_states[call_sid] = {
                'phone': caller_phone,
                'started': True,
                'tenant_info': tenant_info
            }
            
            response = VoiceResponse()
            
            # Temporarily remove recording to test if it's causing issues
            # response.record(
            #     max_length=1800,  # 30 minutes max
            #     play_beep=False,
            #     record_on_answer=True
            # )
            
            # Time-based greeting with natural energy
            eastern = pytz.timezone('US/Eastern')
            current_time = datetime.now(eastern)
            current_hour = current_time.hour
            
            if 5 <= current_hour < 12:
                time_greeting = "Good morning"
            elif 12 <= current_hour < 17:
                time_greeting = "Good afternoon"
            else:
                time_greeting = "Good evening"
            
            greeting_text = f"{time_greeting}! You've reached Grinberg Management, I'm Chris, and I'm excited to help you today! What can I do for you?"
            
            # Try ElevenLabs for natural voice
            audio_url = generate_elevenlabs_audio(greeting_text)
            if audio_url:
                # Use proper domain for audio serving
                replit_domain = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'
                full_audio_url = f"https://{replit_domain}{audio_url}"
                response.play(full_audio_url)
            else:
                # Fallback to Twilio voice
                response.say(greeting_text, voice='Polly.Matthew-Neural')
            
            # Wait for speech input with ultra-fast timeouts for instant responses
            response.gather(
                input='speech',
                action='/continue-conversation',
                timeout=2,  # Ultra-short timeout for instant feel
                speech_timeout=1,  # Maximum speed speech detection
                language='en-US'
            )
            
            # Chris checks in after 5 seconds of silence
            checkin_text = "I'm still here! What can I help you with today?"
            checkin_audio = generate_elevenlabs_audio(checkin_text)
            if checkin_audio:
                replit_domain = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'
                full_audio_url = f"https://{replit_domain}{checkin_audio}"
                response.play(full_audio_url)
            else:
                response.say(checkin_text, voice='Polly.Matthew-Neural')
            
            # Give another chance to respond with ultra-fast timeouts
            response.gather(
                input='speech',
                action='/continue-conversation',
                timeout=3,  # Ultra-short timeout for faster interaction
                speech_timeout=1.5,  # Maximum speed speech detection
                language='en-US'
            )
            
            logger.info(f"Intelligent conversation initiated for {caller_phone}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Call handler error: {e}", exc_info=True)
            response = VoiceResponse()
            error_text = "I'm sorry, we're having technical issues. Please call back in a moment."
            response.say(error_text, voice='Polly.Matthew-Neural')
            return str(response)
    
    @app.route('/handle-speech/<call_sid>', methods=['POST'])
    def handle_speech_input(call_sid):
        """Handle speech input with intelligent AI processing"""
        try:
            speech_result = request.values.get('SpeechResult', '').strip()
            logger.info(f"DEBUG: Received speech for call {call_sid}: '{speech_result}'")
            
            # Log all request values for debugging
            logger.info(f"DEBUG: All request values: {dict(request.values)}")
            
            response = VoiceResponse()
            
            if not speech_result:
                logger.warning(f"No speech detected for call {call_sid}")
                no_speech_text = "I didn't quite catch that. Let me connect you with our amazing team at (718) 414-6984!"
                response.say(no_speech_text, voice='Polly.Matthew-Neural')
                response.dial('(718) 414-6984')
                return str(response)
            
            # Check for instant cached responses first (FASTEST PATH)
            user_lower = speech_result.lower().strip()
            instant_audio_url = None
            ai_response = None
            
            logger.info(f"Checking instant responses for: '{user_lower}'")
            for key, response_data in INSTANT_RESPONSES.items():
                if key in user_lower:
                    ai_response = response_data["text"]
                    instant_audio_url = response_data["audio"]
                    logger.info(f"INSTANT MATCH! Key: {key}, Audio: {instant_audio_url}")
                    break
            
            # If no instant response, generate AI response
            if not ai_response:
                logger.info(f"No instant match, generating AI response for: '{speech_result}'")
                ai_response = generate_intelligent_response(speech_result, call_sid)
            
            logger.info(f"Final AI response: {ai_response}")
            
            # Use pre-generated audio or ElevenLabs
            if instant_audio_url:
                replit_domain = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'
                full_audio_url = f"https://{replit_domain}{instant_audio_url}"
                response.play(full_audio_url)
                logger.info(f"Playing instant audio: {full_audio_url}")
            else:
                # Generate ElevenLabs audio for new responses
                audio_url = generate_elevenlabs_audio(ai_response)
                if audio_url:
                    replit_domain = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'
                    full_audio_url = f"https://{replit_domain}{audio_url}"
                    response.play(full_audio_url)
                else:
                    response.say(ai_response, voice='Polly.Matthew-Neural')
            
            # Check if this needs transfer based on AI response or user request
            if any(word in speech_result.lower() for word in ['transfer', 'human', 'person', 'manager', 'speak to someone']):
                transfer_text = "Perfect! I'm connecting you with Diane or Janier right now!"
                response.say(transfer_text, voice='Polly.Matthew-Neural')
                response.dial('(718) 414-6984')
            elif any(word in ai_response.lower() for word in ['transfer', '414-6984', 'connect you']):
                response.dial('(718) 414-6984')
            else:
                # Continue conversation - gather more input
                response.gather(
                    input='speech',
                    action=f'/handle-speech/{call_sid}',
                    method='POST',
                    timeout=20,  # Longer timeout for natural conversation
                    speech_timeout=4,  # Shorter speech timeout for quicker response
                    language='en-US'
                )
                
                # Only say goodbye if they haven't responded for a while
                still_here_text = "I'm still here if you need anything else! Or I can connect you with our team at (718) 414-6984."
                response.say(still_here_text, voice='Polly.Matthew-Neural')
                
                # Give one more chance to continue
                response.gather(
                    input='speech',
                    action=f'/handle-speech/{call_sid}',
                    method='POST',
                    timeout=10,
                    speech_timeout=3,
                    language='en-US'
                )
                
                # Final fallback
                goodbye_text = "Thank you for calling Grinberg Management! Have a wonderful day!"
                response.say(goodbye_text, voice='Polly.Matthew-Neural')
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Speech handler error for call {call_sid}: {e}", exc_info=True)
            response = VoiceResponse()
            
            # Graceful error handling - don't disconnect, offer help
            error_text = "I'm having a small technical moment. Let me help you another way - what can I assist you with today?"
            response.say(error_text, voice='Polly.Matthew-Neural')
            
            # Give another chance instead of immediate transfer
            response.gather(
                input='speech',
                action=f'/handle-speech/{call_sid}',
                method='POST',
                timeout=10,
                speech_timeout=3,
                language='en-US'
            )
            
            # If still no response, then transfer
            transfer_text = "Let me connect you with our team at (718) 414-6984!"
            response.say(transfer_text, voice='Polly.Matthew-Neural')
            response.dial('(718) 414-6984')
            return str(response)
    
    @app.route('/static/<filename>')
    def serve_audio(filename):
        """Serve generated audio files"""
        from flask import send_from_directory
        return send_from_directory('static', filename)
    
    @app.route('/continue-conversation', methods=['POST'])
    def continue_conversation():
        """Continue conversation - no automatic transfers"""
        from models import db, ActiveCall
        try:
            speech_result = request.values.get('SpeechResult', '').strip()
            call_sid = request.values.get('CallSid', 'Unknown')
            caller_phone = request.values.get('From', 'Unknown')
            logger.info(f"Continue conversation - Speech: '{speech_result}', Call: {call_sid}, From: {caller_phone}")
            
            response = VoiceResponse()
            
            if speech_result:
                # Check for instant cached responses first (FASTEST)
                user_lower = speech_result.lower().strip()
                instant_audio_url = None
                ai_response = None
                
                # Minimal debug logging for speed
                logger.info(f"Checking instant responses for: '{user_lower}'")
                
                for key, response_data in INSTANT_RESPONSES.items():
                    if key in user_lower:
                        ai_response = response_data["text"]
                        instant_audio_url = response_data["audio"]
                        logger.info(f"INSTANT MATCH: {key}")
                        break
                
                # Skip logging for speed when no instant match
                
                # If no instant response, generate AI response with caller context
                if not ai_response:
                    ai_response = generate_intelligent_response(speech_result, call_sid)
                
                logger.info(f"AI response: {ai_response}")
                
                # Use pre-generated audio or generate new one
                if instant_audio_url:
                    replit_domain = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'
                    full_audio_url = f"https://{replit_domain}{instant_audio_url}"
                    response.play(full_audio_url)
                else:
                    audio_url = generate_elevenlabs_audio(ai_response)
                    if audio_url:
                        replit_domain = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'
                        full_audio_url = f"https://{replit_domain}{audio_url}"
                        response.play(full_audio_url)
                    else:
                        response.say(ai_response, voice='Polly.Matthew-Neural')
            
            # Update active call status asynchronously to avoid blocking response
            # Skip database updates for instant responses to maintain speed
            if not instant_audio_url:
                try:
                    with app.app_context():
                        active_call = ActiveCall.query.filter_by(call_sid=call_sid).first()
                        if active_call:
                            active_call.last_activity = datetime.utcnow()
                            active_call.current_action = f"Discussing: {speech_result[:30]}..."
                            db.session.commit()
                except Exception as e:
                    logger.error(f"Database error updating call: {e}")
            
            # Continue conversation with ultra-fast timeouts for maximum speed
            response.gather(
                input='speech',
                action='/continue-conversation',
                method='POST',
                timeout=15,  # Reasonable timeout for natural conversation
                speech_timeout=1.5,  # Ultra-fast speech detection for immediate responses
                language='en-US'
            )
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Simple response error: {e}")
            response = VoiceResponse()
            response.say("Let me connect you with our team at (718) 414-6984.", voice='Polly.Matthew-Neural')
            response.dial('(718) 414-6984')
            return str(response)
    
    @app.route('/')
    def dashboard():
        """Dashboard showing intelligent AI status and call recordings"""
        from models import db, CallRecord, ActiveCall
        from datetime import datetime, timedelta
        
        # Get search parameters
        search_phone = request.args.get('phone', '').strip()
        search_date = request.args.get('date', '').strip()
        
        # Clean up old active calls (older than 5 minutes)
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        old_calls = ActiveCall.query.filter(ActiveCall.last_activity < cutoff_time).all()
        for old_call in old_calls:
            # Move to call records
            call_record = CallRecord(
                call_sid=old_call.call_sid,
                phone_number=old_call.phone_number,
                caller_name=old_call.caller_name,
                tenant_unit=old_call.tenant_unit,
                tenant_id=old_call.tenant_id,
                start_time=old_call.start_time,
                end_time=datetime.utcnow(),
                duration=int((datetime.utcnow() - old_call.start_time).total_seconds()),
                call_status='completed'
            )
            db.session.add(call_record)
            db.session.delete(old_call)
        db.session.commit()
        
        # Get active calls from database
        active_calls_db = ActiveCall.query.all()
        
        # Get call recordings from database with search filters
        query = CallRecord.query
        if search_phone:
            query = query.filter(CallRecord.phone_number.contains(search_phone))
        if search_date:
            search_datetime = datetime.strptime(search_date, '%Y-%m-%d').date()
            query = query.filter(db.func.date(CallRecord.start_time) == search_datetime)
        
        call_recordings_db = query.order_by(CallRecord.start_time.desc()).limit(50).all()
        
        # Convert timezone to EST for display
        eastern = pytz.timezone('US/Eastern')
        
        return render_template('intelligent_dashboard.html',
                             openai_connected=bool(OPENAI_API_KEY),
                             elevenlabs_connected=bool(ELEVENLABS_API_KEY),
                             active_calls=active_calls_db,
                             call_recordings=call_recordings_db,
                             search_phone=search_phone,
                             search_date=search_date)
    
    @app.route('/api/active-calls')
    def api_active_calls():
        """API endpoint for real-time active calls data"""
        from models import db, ActiveCall, CallRecord
        from datetime import datetime, timedelta
        
        # Clean up old active calls (older than 5 minutes)
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        old_calls = ActiveCall.query.filter(ActiveCall.last_activity < cutoff_time).all()
        for old_call in old_calls:
            # Move to call records
            call_record = CallRecord(
                call_sid=old_call.call_sid,
                phone_number=old_call.phone_number,
                caller_name=old_call.caller_name,
                tenant_unit=old_call.tenant_unit,
                tenant_id=old_call.tenant_id,
                start_time=old_call.start_time,
                end_time=datetime.utcnow(),
                duration=int((datetime.utcnow() - old_call.start_time).total_seconds()),
                call_status='completed'
            )
            db.session.add(call_record)
            db.session.delete(old_call)
        db.session.commit()
        
        # Get current active calls
        active_calls = ActiveCall.query.all()
        calls_data = []
        eastern = pytz.timezone('US/Eastern')
        
        for call in active_calls:
            # Convert to Eastern time for display
            eastern_time = call.start_time.replace(tzinfo=pytz.UTC).astimezone(eastern)
            duration = datetime.utcnow() - call.start_time
            duration_str = f"{int(duration.total_seconds() // 60)}m {int(duration.total_seconds() % 60)}s"
            
            calls_data.append({
                'call_sid': call.call_sid[-8:],
                'phone': call.phone_number,
                'caller_name': call.caller_name or 'Unknown Caller',
                'tenant_unit': call.tenant_unit,
                'start_time': eastern_time.strftime('%I:%M %p'),
                'duration': duration_str,
                'status': call.call_status,
                'current_action': call.current_action or 'In conversation'
            })
        return jsonify(calls_data)
    
    @app.route('/call-status', methods=['POST'])
    def call_status():
        """Handle call status updates from Twilio"""
        from models import db, ActiveCall, CallRecord
        
        call_sid = request.values.get('CallSid', '')
        call_status = request.values.get('CallStatus', '')
        duration = request.values.get('CallDuration', '0')
        
        logger.info(f"Call status update: {call_sid} - {call_status}")
        
        if call_status in ['completed', 'failed', 'busy', 'no-answer']:
            try:
                with app.app_context():
                    # Move from active calls to call records
                    active_call = ActiveCall.query.filter_by(call_sid=call_sid).first()
                    if active_call:
                        # Create call record
                        call_record = CallRecord(
                            call_sid=call_sid,
                            phone_number=active_call.phone_number,
                            caller_name=active_call.caller_name,
                            tenant_unit=active_call.tenant_unit,
                            tenant_id=active_call.tenant_id,
                            start_time=active_call.start_time,
                            end_time=datetime.utcnow(),
                            duration=int(duration),
                            call_status=call_status
                        )
                        db.session.add(call_record)
                        
                        # Remove from active calls
                        db.session.delete(active_call)
                        db.session.commit()
                        
                        logger.info(f"Call {call_sid} moved to call records")
            except Exception as e:
                logger.error(f"Error updating call status: {e}")
        
        return '', 200
    
    @app.route('/test-intelligent')
    def test_intelligent():
        """Test intelligent AI responses"""
        test_input = request.args.get('input', 'Hello, how are you?')
        response = generate_intelligent_response(test_input, 'test')
        return jsonify({'input': test_input, 'intelligent_response': response})
    
    @app.route('/api/recordings/search')
    def search_recordings_api():
        """API endpoint for searching call recordings"""
        try:
            search_phone = request.args.get('phone', '').strip()
            search_date = request.args.get('date', '').strip()
            search_text = request.args.get('text', '').strip()
            
            filtered_recordings = []
            for call_sid, recording in call_recordings.items():
                # Apply phone number filter
                if search_phone and search_phone not in recording.get('phone', ''):
                    continue
                    
                # Apply date filter
                if search_date:
                    recording_date = recording.get('timestamp', '')[:10]
                    if search_date != recording_date:
                        continue
                
                # Apply transcription text search
                if search_text:
                    transcription = recording.get('transcription', '').lower()
                    if search_text.lower() not in transcription:
                        continue
                
                filtered_recordings.append({
                    'call_sid': call_sid,
                    'phone': recording.get('phone', 'Unknown'),
                    'duration': recording.get('duration', '0'),
                    'timestamp': recording.get('timestamp', ''),
                    'recording_url': recording.get('url', ''),
                    'transcription': recording.get('transcription', ''),
                    'tenant_name': recording.get('tenant_info', {}).get('name', 'Unknown Caller') if recording.get('tenant_info') else 'Unknown Caller'
                })
            
            # Sort by timestamp (newest first)
            filtered_recordings.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return jsonify({
                'recordings': filtered_recordings[:50],  # Limit to 50 results
                'total_found': len(filtered_recordings),
                'total_recordings': len(call_recordings)
            })
            
        except Exception as e:
            logger.error(f"Search API error: {e}")
            return jsonify({'error': 'Search failed'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)