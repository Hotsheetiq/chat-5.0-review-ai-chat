import os
import json
import base64
import asyncio
import logging
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
        
        # Professional greeting for voice assistant
        response.say("Hello, and thank you for calling our property management office. "
                    "I'm your AI assistant and I can help with maintenance requests, "
                    "leasing information, and general property questions. "
                    "How can I help you today?")
        
        # For now, provide a simple response system
        # In production, this would connect to the real-time AI system
        response.gather(
            input='speech',
            timeout=10,
            speech_timeout='auto',
            action='/process-speech',
            method='POST'
        )
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, we're experiencing technical difficulties. Please try calling back later.")
        return str(response)

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
            response.say("I didn't catch that. Could you please repeat your request?")
            response.gather(
                input='speech',
                timeout=10,
                speech_timeout='auto',
                action='/process-speech',
                method='POST'
            )
            return str(response)
        
        # Simple keyword-based processing (would be replaced with OpenAI in production)
        speech_lower = speech_result.lower()
        
        # Look up caller information
        caller_info = {"phone": caller_phone, "is_tenant": False, "tenant_data": None}
        
        if rent_manager:
            try:
                # This would be an async call in production, simplified for demo
                # tenant_data = await rent_manager.lookup_tenant_by_phone(caller_phone)
                # For now, simulate tenant lookup
                logger.info(f"Looking up tenant for phone: {caller_phone}")
            except Exception as e:
                logger.error(f"Error looking up tenant: {e}")
        
        # Process different types of requests
        if any(word in speech_lower for word in ['maintenance', 'repair', 'broken', 'fix']):
            response.say("I understand you have a maintenance request. "
                        "I'm creating a service ticket for you right now. "
                        "Our maintenance team will follow up within 24 hours. "
                        "Is there anything else I can help you with?")
                        
        elif any(word in speech_lower for word in ['lease', 'rent', 'available', 'apartment']):
            response.say("Thank you for your interest in our property. "
                        "I'm creating a follow-up task for our leasing team. "
                        "Someone will contact you within one business day with "
                        "information about available units. "
                        "Is there anything else I can help you with?")
                        
        elif any(word in speech_lower for word in ['hours', 'office', 'contact']):
            hours_info = property_data.get_office_hours()
            response.say(f"Our office hours are {hours_info}. "
                        "Is there anything else I can help you with?")
                        
        else:
            response.say("Thank you for your call. I've made a note of your request "
                        "and someone from our team will follow up with you shortly. "
                        "Is there anything else I can help you with?")
        
        # Give option to continue or end call
        response.gather(
            input='speech',
            timeout=5,
            speech_timeout='auto',
            action='/process-speech',
            method='POST'
        )
        
        response.say("Thank you for calling. Have a great day!")
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        response = VoiceResponse()
        response.say("I'm sorry, I had trouble processing your request. "
                    "Please call back and try again.")
        return str(response)

if __name__ == '__main__':
    # For development
    socketio.run(app, host='0.0.0.0', port=PORT, debug=True, use_reloader=True, log_output=True)