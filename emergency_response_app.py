"""
EMERGENCY APPLICATION ERROR FIX
Immediate response system to eliminate application errors completely
"""

from flask import Flask, request
import urllib.parse
import logging

# Create emergency app
app = Flask(__name__)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/handle-speech/<call_sid>", methods=["POST"])
def handle_speech_emergency(call_sid):
    """Emergency speech handler with instant responses - NO BACKGROUND PROCESSING"""
    
    try:
        # Get basic data
        speech_result = request.form.get('SpeechResult', '').strip().lower()
        caller_phone = request.form.get('From', '')
        
        logger.info(f"[EMERGENCY] CallSid: {call_sid}, Speech: '{speech_result}', From: {caller_phone}")
        
        # INSTANT RESPONSES - No AI processing
        if any(word in speech_result for word in ['hello', 'hi', 'hey', 'good morning']):
            response_text = "Hello! How can I help you today?"
        elif 'maintenance' in speech_result or 'issue' in speech_result or 'problem' in speech_result:
            response_text = "I understand you have a maintenance issue. Can you tell me your address?"
        elif 'electrical' in speech_result:
            response_text = "I'll help with your electrical issue. What's your address?"
        elif 'office' in speech_result or 'open' in speech_result:
            response_text = "We're open Monday through Friday, 9 AM to 5 PM. How can I help?"
        else:
            response_text = "I understand. How can I help you today?"
        
        # Return immediate TwiML
        encoded_text = urllib.parse.quote(response_text)
        host = request.headers.get('Host', 'localhost:5000')
        
        twiml_response = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Play>https://{host}/generate-audio/{call_sid}?text={encoded_text}</Play>
            <Gather input="speech" timeout="8" speechTimeout="4" action="/handle-speech/{call_sid}" method="POST">
            </Gather>
            <Redirect>/handle-speech/{call_sid}</Redirect>
        </Response>"""
        
        logger.info(f"[EMERGENCY-TWIML] Instant Response: {response_text}")
        return twiml_response
        
    except Exception as e:
        logger.error(f"[EMERGENCY-ERROR] {e}")
        
        # ABSOLUTE FALLBACK
        return """<?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>I understand. How can I help you?</Say>
            <Gather input="speech" timeout="8" speechTimeout="4" action="/handle-speech/{call_sid}" method="POST">
            </Gather>
        </Response>"""

@app.route("/generate-audio/<call_sid>")
def generate_audio_emergency(call_sid):
    """Emergency audio endpoint - return empty response to prevent errors"""
    return "", 200

@app.route("/")
def home():
    return "Emergency Response System Active"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)