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
import pytz
import requests
import base64
import asyncio
from rent_manager import RentManagerAPI

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
if os.environ.get("RENT_MANAGER_USERNAME") and os.environ.get("RENT_MANAGER_PASSWORD"):
    # Create credentials string - location ID will default to 1 if not numeric
    location_id = os.environ.get("RENT_MANAGER_LOCATION_ID", "1")
    rent_manager_credentials = f"{os.environ.get('RENT_MANAGER_USERNAME')}:{os.environ.get('RENT_MANAGER_PASSWORD')}:{location_id}"
    rent_manager = RentManagerAPI(rent_manager_credentials)

# Call state tracking
call_states = {}
conversation_history = {}
call_recordings = {}  # Store call recordings for dashboard access

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
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
    
    def generate_elevenlabs_audio(text, voice_id="1aaKc4GWOfIKpc3svAJd"):
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
                    "stability": 0.7,          # More stable for consistent speech
                    "similarity_boost": 0.75,  # Good voice similarity
                    "style": 0.3,              # Slightly more expressive
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=5)  # Much faster timeout
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
    
    def generate_intelligent_response(user_input, call_sid=None):
        """Generate intelligent AI response using GPT-4o"""
        try:
            if not openai_client:
                logger.error("No OpenAI client available")
                return get_smart_fallback(user_input)
            
            logger.info(f"Generating GPT-4o response for: {user_input}")
            
            # Build conversation context with natural ChatGPT-style prompting
            messages = [
                {
                    "role": "system",
                    "content": """You are Chris, the AI Assistant for Grinberg Management. You sound exactly like ChatGPT - natural, intelligent, and genuinely conversational.

PERSONALITY & TONE:
- Talk like a real person, not a formal assistant
- Be friendly and helpful without sounding scripted
- Use natural speech patterns: "Oh, absolutely!" "That's a great question!" "Let me help with that"
- Show genuine interest and understanding
- Respond like you're having a real conversation with a friend

BUSINESS INFO:
- Office: 31 Port Richmond Avenue
- Hours: Monday-Friday, 9 AM - 5 PM Eastern Time
- IMPORTANT: Check current time! If outside office hours, say "We're closed right now, but I'm here to help!"
- After hours: Take messages, handle maintenance emergencies, create service requests
- Transfer to (718) 414-6984 for Diane or Janier when needed (office hours only)
- Handle maintenance requests with empathy regardless of time
- We work with Section 8 tenants
- We do not work with cash tenants or other rental assistance programs

TENANT CONTEXT:
- If caller is a known tenant, greet them personally and reference their unit
- For maintenance requests from tenants, create service issues in Rent Manager
- For prospects, collect basic information and create worker tasks for follow-up
- If phone number lookup fails, ask caller for their unit number to provide personalized help
- Always be helpful whether caller is in system or not

CONVERSATIONAL EXAMPLES:
- Instead of: "We're open Monday through Friday, 9 AM to 5 PM Eastern Time."
- Say: "Oh sure! We're here Monday through Friday, 9 to 5. What can I help you with?"

- Instead of: "I can assist you with maintenance requests."
- Say: "Absolutely! What's going on? I'm here to help get that sorted out."

Keep responses under 20 words for faster delivery. Sound natural and conversational. Use contractions and casual phrases like ChatGPT does."""
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
            
            # Generate response using GPT-4o with speed-optimized parameters  
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # Latest OpenAI model for best conversation
                messages=[{"role": msg["role"], "content": msg["content"]} for msg in messages],
                max_tokens=40,  # Even shorter for sub-2-second responses  
                temperature=0.5,   # Lower for faster, more focused responses
                presence_penalty=0.1,  # Reduce processing overhead
                frequency_penalty=0.2  # Minimal repetition control
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
            
            # Skip initial tenant lookup for faster greeting - will handle during conversation
            tenant_info = None
            
            # Initialize call state with tenant info
            call_states[call_sid] = {
                'phone': caller_phone,
                'started': True,
                'tenant_info': tenant_info
            }
            
            response = VoiceResponse()
            
            # Start call recording for all calls
            response.record(
                action='/recording-status',
                method='POST',
                max_length=1800,  # 30 minutes max recording
                play_beep=False,  # No recording beep for natural conversation
                record_on_answer=True,
                transcribe=True,  # Enable transcription for better record keeping
                transcribe_callback='/transcription-callback'
            )
            
            # Cheerful greeting from Chris
            greeting = "Hi there, you have reached Grinberg Management, I'm Chris, how can I help?"
            
            # Temporarily use Twilio voice to test if issue is with audio serving
            response.say(greeting, voice='Polly.Matthew-Neural')
            
            # Gather input for intelligent conversation
            response.gather(
                input='speech',
                action=f'/handle-speech/{call_sid}',
                method='POST',
                timeout=10,
                speech_timeout='auto'
            )
            
            # Fallback if no speech detected  
            fallback_text = "I'm sorry, I didn't catch that. Let me connect you with our wonderful team at (718) 414-6984!"
            response.say(fallback_text, voice='Polly.Matthew-Neural')
            response.dial('(718) 414-6984')
            
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
            logger.info(f"Speech from caller: {speech_result}")
            
            response = VoiceResponse()
            
            if not speech_result:
                no_speech_text = "I didn't quite catch that. Let me connect you with our amazing team at (718) 414-6984!"
                response.say(no_speech_text, voice='Polly.Matthew-Neural')
                response.dial('(718) 414-6984')
                return str(response)
            
            # Generate intelligent AI response using GPT-4o
            ai_response = generate_intelligent_response(speech_result, call_sid)
            logger.info(f"Intelligent AI response: {ai_response}")
            
            # Use Twilio voice for Chris
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
                    timeout=15,  # Longer timeout for natural conversation
                    speech_timeout='auto'
                )
                
                # Only say goodbye if they haven't responded for a while
                still_here_text = "I'm still here if you need anything else! Or I can connect you with our team at (718) 414-6984."
                response.say(still_here_text, voice='Polly.Matthew-Neural')
                
                # Give one more chance to continue
                response.gather(
                    input='speech',
                    action=f'/handle-speech/{call_sid}',
                    method='POST',
                    timeout=8,
                    speech_timeout='auto'
                )
                
                # Final fallback
                goodbye_text = "Thank you for calling Grinberg Management! Have a wonderful day!"
                response.say(goodbye_text, voice='Polly.Matthew-Neural')
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Speech handler error: {e}", exc_info=True)
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
                speech_timeout='auto'
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
    
    @app.route('/')
    def dashboard():
        """Dashboard showing intelligent AI status and call recordings"""
        recent_calls = []
        for call_sid, state in list(call_states.items())[-5:]:
            recent_calls.append({
                'call_sid': call_sid[-8:],
                'phone': state.get('phone', 'Unknown'),
                'status': 'Active' if state.get('started') else 'Ended'
            })
        
        # Get search parameters
        search_phone = request.args.get('phone', '').strip()
        search_date = request.args.get('date', '').strip()
        
        # Filter call recordings based on search criteria
        filtered_recordings = []
        for call_sid, recording in call_recordings.items():
            # Apply phone number filter
            if search_phone and search_phone not in recording.get('phone', ''):
                continue
                
            # Apply date filter
            if search_date:
                recording_date = recording.get('timestamp', '')[:10]  # Extract YYYY-MM-DD
                if search_date != recording_date:
                    continue
            
            filtered_recordings.append({
                'call_sid': call_sid[-8:],
                'phone': recording.get('phone', 'Unknown'),
                'duration': recording.get('duration', '0'),
                'timestamp': recording.get('timestamp', ''),
                'recording_url': recording.get('url', ''),
                'transcription': recording.get('transcription', '')[:200] if recording.get('transcription') else 'Processing...',
                'tenant_name': recording.get('tenant_info', {}).get('name', 'Unknown Caller') if recording.get('tenant_info') else 'Unknown Caller'
            })
        
        # Sort by timestamp (newest first) and limit to last 50
        filtered_recordings.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_recordings = filtered_recordings[:50]
        
        return render_template('intelligent_dashboard.html',
                             openai_connected=bool(OPENAI_API_KEY),
                             elevenlabs_connected=bool(ELEVENLABS_API_KEY),
                             active_calls=len([s for s in call_states.values() if s.get('started')]),
                             recent_calls=recent_calls,
                             recent_recordings=recent_recordings,
                             search_phone=search_phone,
                             search_date=search_date,
                             total_recordings=len(call_recordings))
    
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