#!/usr/bin/env python3
"""
Simple webhook test to verify Twilio speech recognition
"""
import os
from flask import Flask, request

app = Flask(__name__)

@app.route("/test-voice", methods=["POST"])
def test_voice():
    """Simple voice test endpoint"""
    print("=== VOICE TEST ENDPOINT ===")
    all_params = dict(request.values)
    for key, value in all_params.items():
        print(f"{key}: {value}")
    
    return """<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="Polly.Matthew-Neural">Hello! This is a speech test. Please say something and I'll try to capture it.</Say>
        <Gather input="speech" timeout="10" speechTimeout="auto" language="en-US" action="/test-speech">
        </Gather>
        <Say voice="Polly.Matthew-Neural">I didn't hear anything. Goodbye.</Say>
    </Response>"""

@app.route("/test-speech", methods=["POST"])
def test_speech():
    """Test speech capture"""
    print("=== SPEECH TEST ENDPOINT ===")
    speech_result = request.values.get("SpeechResult", "")
    confidence = request.values.get("Confidence", "")
    
    print(f"Speech Result: '{speech_result}'")
    print(f"Confidence: {confidence}")
    
    all_params = dict(request.values)
    print("All parameters:")
    for key, value in all_params.items():
        print(f"  {key}: {value}")
    
    if speech_result:
        response_text = f"I heard you say: {speech_result}. That worked perfectly!"
    else:
        response_text = "I didn't capture any speech. There might be a configuration issue."
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <Response>
        <Say voice="Polly.Matthew-Neural">{response_text}</Say>
    </Response>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)