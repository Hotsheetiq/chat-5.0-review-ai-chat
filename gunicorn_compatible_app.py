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

def generate_mike_response(text_input: str) -> str:
    """Generate Mike's enthusiastic response"""
    try:
        if not openai_client:
            return "I'm super excited to help! Let me transfer you to our amazing team at (718) 414-6984!"
            
        system_prompt = """You are Mike from Grinberg Management - super bubbly, happy, and enthusiastic! You LOVE helping people and you're genuinely excited about everything!

Keep responses under 60 words for phone calls. Be naturally conversational and full of positive energy!

Key info:
- Office: 31 Port Richmond Ave, hours 9-5 Monday-Friday Eastern Time  
- For any transfers: "Let me get you to Diane or Janier at (718) 414-6984!"
- Use exclamation points and positive words like "awesome," "fantastic," "love"
- Sound genuinely happy and bubbly"""

        response = openai_client.chat.completions.create(
            model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text_input}
            ],
            max_tokens=60,
            temperature=0.8
        )
        
        return response.choices[0].message.content or "I'm so excited to help you!"
        
    except Exception as e:
        logger.error(f"OpenAI error: {e}")
        return "I'm having a little technical hiccup, but I'm still super excited to help!"

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
                response.say("Hi! Thanks for calling Grinberg Management! I'm having technical issues right now, but I'd love to help! Please leave a message after the beep and we'll get back to you super quickly!",
                            voice='Polly.Joanna-Neural')
                response.record(timeout=30, transcribe=False)
                return str(response)
            
            # Store call info
            call_states[call_sid] = {
                'phone': caller_phone,
                'started': True
            }
            
            # Mike's enthusiastic greeting with conversational flow
            greeting = "It's a great day here at Grinberg Management! My name is Mike and I'm super excited to help you today! What can I do for you?"
            
            response.say(greeting, voice='Polly.Matthew-Neural')
            
            # Gather input for conversation
            response.gather(
                input='speech',
                action=f'/handle-speech/{call_sid}',
                method='POST',
                timeout=10,
                speech_timeout='auto'
            )
            
            # Fallback if no speech detected
            response.say("I'm sorry, I didn't catch that! Let me transfer you to our awesome team at (718) 414-6984!",
                        voice='Polly.Matthew-Neural')
            response.dial('(718) 414-6984')
            
            logger.info(f"Call initiated for {caller_phone}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Call handler error: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("Sorry, we're having technical difficulties. Please call back shortly.",
                        voice='Polly.Matthew-Neural')
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
                response.say("I'm sorry, I didn't catch that! Let me get you to our fantastic team at (718) 414-6984!",
                            voice='Polly.Matthew-Neural')
                response.dial('(718) 414-6984')
                return str(response)
            
            # Generate Mike's response
            ai_response = generate_mike_response(speech_result)
            logger.info(f"Mike's response: {ai_response}")
            
            response.say(ai_response, voice='Polly.Matthew-Neural')
            
            # Check if this needs transfer or more conversation
            if any(word in speech_result.lower() for word in ['transfer', 'human', 'person', 'manager', 'speak to someone']):
                response.say("Absolutely! Let me get you to Diane or Janier right away!",
                            voice='Polly.Matthew-Neural')
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
                response.say("Thanks so much for calling! If you need anything else, we're here to help at (718) 414-6984!",
                            voice='Polly.Matthew-Neural')
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Speech handler error: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("Let me transfer you to our team at (718) 414-6984!",
                        voice='Polly.Matthew-Neural')
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
    
    @app.route('/test-mike')
    def test_mike():
        """Test Mike's responses"""
        test_input = request.args.get('input', 'I need help with my apartment')
        response = generate_mike_response(test_input)
        return jsonify({'input': test_input, 'mike_response': response})
    
    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=PORT, debug=True)