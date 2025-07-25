#!/usr/bin/env python3
"""
Debug Twilio speech recognition issues
"""
from flask import Flask, request
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route("/debug-voice", methods=["POST"])
def debug_voice():
    """Debug voice endpoint with detailed logging"""
    logger.info("=== DEBUG VOICE ENDPOINT ===")
    
    # Log all parameters
    all_params = dict(request.values)
    for key, value in all_params.items():
        logger.info(f"{key}: {value}")
    
    # Simple TwiML with minimal Gather settings
    return """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="Polly.Matthew">Hello! This is a speech test. Please say the word 'hello' clearly.</Say>
        <Gather input="speech" timeout="10" speechTimeout="2" action="/debug-speech" method="POST">
        </Gather>
        <Say voice="Polly.Matthew">No speech detected. Goodbye.</Say>
    </Response>"""

@app.route("/debug-speech", methods=["POST"])
def debug_speech():
    """Debug speech capture with detailed logging"""
    logger.info("=== DEBUG SPEECH CAPTURE ===")
    
    # Get speech result
    speech_result = request.values.get("SpeechResult", "")
    confidence = request.values.get("Confidence", "")
    
    logger.info(f"Speech Result: '{speech_result}'")
    logger.info(f"Confidence: '{confidence}'")
    
    # Log all parameters
    all_params = dict(request.values)
    logger.info("All speech parameters:")
    for key, value in all_params.items():
        logger.info(f"  {key}: {value}")
    
    if speech_result:
        message = f"SUCCESS! I heard: {speech_result} with confidence {confidence}"
    else:
        message = "FAILED: No speech was captured. This indicates a Twilio configuration issue."
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="Polly.Matthew">{message}</Say>
    </Response>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)