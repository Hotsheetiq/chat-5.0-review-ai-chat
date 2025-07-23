"""
Gunicorn-compatible Twilio Media Streams implementation
Uses standard HTTP endpoints instead of WebSockets to work with gunicorn
"""

import os
import json
import base64
import logging
from flask import Flask, request, render_template, jsonify
from twilio.twiml.voice_response import VoiceResponse, Connect, Start, Stream, Say
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Call state tracking
call_states = {}

def generate_sarah_response(text_input: str) -> str:
    """Generate Sarah's enthusiastic response"""
    try:
        if not openai_client:
            return "Oh WOW, I'm absolutely THRILLED you called! Let me get you to our incredible team at (718) 414-6984!"
            
        system_prompt = """You are Sarah from Grinberg Management - SUPER excited, bubbly, and absolutely LOVE helping people! You're genuinely thrilled about everything and use lots of exclamation points!

Keep responses under 40 words but pack them with energy! Sound like you just had the best coffee ever!

Key info:
- Office: 31 Port Richmond Ave, hours 9-5 Monday-Friday Eastern Time  
- For transfers: "I'd love to get you to Diane or Janier at (718) 414-6984!"
- Use words like "awesome," "fantastic," "amazing," "love," "excited"
- Sound like you're bouncing with enthusiasm!"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_input}
            ],
            max_tokens=60,
            temperature=0.8
        )
        
        return response.choices[0].message.content or "Oh my gosh, I'm SO excited to help you! This is fantastic!"
        
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return "Ooh, I'm having a tiny technical moment, but I'm still absolutely THRILLED to help you! This is so exciting!"

def create_app():
    """Create Flask app compatible with gunicorn"""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    
    @app.route('/incoming-call', methods=['GET', 'POST'])
    def handle_incoming_call():
        """Handle incoming calls - simplified approach without WebSockets"""
        try:
            caller_phone = request.values.get('From', 'Unknown')
            call_sid = request.values.get('CallSid', 'Unknown')
            
            logger.info(f"Incoming call from: {caller_phone}, CallSid: {call_sid}")
            
            response = VoiceResponse()
            
            if not OPENAI_API_KEY:
                response.say("Hi there! OH MY GOSH, thank you for calling Grinberg Management! I'm Sarah and I'm having some technical hiccups, but I'm SO excited to help! Leave me a message and I'll get back to you ASAP!",
                            voice='Polly.Joanna-Neural')
                response.record(timeout=30, transcribe=False)
                return str(response)
            
            # Store call info
            call_states[call_sid] = {
                'phone': caller_phone,
                'started': True
            }
            
            # Sarah's natural, bubbly greeting  
            greeting = "Hi there! It's a beautiful day here at Grinberg Management! I'm Sarah, and I'm so happy you called! How can I help you today?"
            
            response.say(greeting, voice='Polly.Joanna-Neural')
            
            # Gather input for conversation
            response.gather(
                input='speech',
                action=f'/handle-speech/{call_sid}',
                method='POST',
                timeout=10,
                speech_timeout='auto'
            )
            
            # Fallback if no speech detected
            response.say("Oh, I'm sorry! I didn't catch what you said. Let me get you to our wonderful team at (718) 414-6984!",
                        voice='Polly.Joanna-Neural')
            response.dial('(718) 414-6984')
            
            logger.info(f"Call initiated for {caller_phone}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Call handler error: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("Oh no! We're having some technical issues right now. Could you try calling back in just a few minutes?",
                        voice='Polly.Joanna-Neural')
            return str(response)
    
    @app.route('/handle-speech/<call_sid>', methods=['POST'])
    def handle_speech(call_sid):
        """Handle speech input from caller"""
        try:
            speech_result = request.values.get('SpeechResult', '')
            caller_phone = call_states.get(call_sid, {}).get('phone', 'Unknown')
            
            logger.info(f"Speech from {caller_phone}: {speech_result}")
            
            response = VoiceResponse()
            
            if not speech_result:
                response.say("Oh, I'm sorry! I didn't quite hear you. Let me connect you with our amazing team at (718) 414-6984!",
                            voice='Polly.Joanna-Neural')
                response.dial('(718) 414-6984')
                return str(response)
            
            # Generate Sarah's response
            ai_response = generate_sarah_response(speech_result)
            logger.info(f"Sarah's response: {ai_response}")
            
            response.say(ai_response, voice='Polly.Joanna-Neural')
            
            # Check if this needs transfer or more conversation
            if any(word in speech_result.lower() for word in ['transfer', 'human', 'person', 'manager', 'speak to someone']):
                response.say("Absolutely! I'm SO excited to get you connected with Diane or Janier right now!",
                            voice='Polly.Joanna-Neural')
                response.dial('(718) 414-6984')
            elif any(word in ai_response.lower() for word in ['transfer', '414-6984']):
                response.dial('(718) 414-6984')
            else:
                # Continue conversation
                response.gather(
                    input='speech',
                    action=f'/handle-speech/{call_sid}',
                    method='POST',
                    timeout=10,
                    speech_timeout='auto'
                )
                
                # Fallback after timeout
                response.say("Thank you so much for calling! If you need anything else, just give us a ring at (718) 414-6984!",
                            voice='Polly.Joanna-Neural')
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Speech handler error: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("Let me get you connected with our team at (718) 414-6984!",
                        voice='Polly.Joanna-Neural')
            response.dial('(718) 414-6984')
            return str(response)
    
    @app.route('/call-status', methods=['POST'])
    def call_status():
        """Handle call status updates"""
        call_sid = request.values.get('CallSid')
        call_status = request.values.get('CallStatus')
        
        logger.info(f"Call {call_sid} status: {call_status}")
        
        if call_sid in call_states and call_status in ['completed', 'failed', 'busy', 'no-answer']:
            del call_states[call_sid]
        
        return '', 200
    
    @app.route('/')
    def dashboard():
        """Dashboard showing system status"""
        recent_calls = [
            {
                'time': '21:51:42',
                'phone': '+1 (347) 743-0880', 
                'call_id': 'CA452aa6a9da28c2de80779fcc1fb58807',
            }
        ]
        
        return render_template('dashboard.html',
                             openai_connected=bool(OPENAI_API_KEY),
                             elevenlabs_connected=bool(ELEVENLABS_API_KEY),
                             recent_calls=recent_calls)
    
    @app.route('/test-sarah')
    def test_sarah():
        """Test Sarah's responses"""
        test_input = request.args.get('input', 'I need help with my apartment')
        response = generate_sarah_response(test_input)
        return jsonify({'input': test_input, 'sarah_response': response})
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT, debug=True)