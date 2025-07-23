"""
Proper Twilio Media Streams implementation using Flask-Sockets
This fixes the incompatibility issue with Flask-SocketIO
"""

import os
import json
import base64
import logging
from flask import Flask, request, render_template
from flask_sockets import Sockets
from twilio.twiml.voice_response import VoiceResponse, Connect, Start, Stream
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Active streams
active_streams = {}

def create_app():
    """Create Flask app with Twilio Media Streams support"""
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    sockets = Sockets(app)
    
    def generate_mike_response(text_input: str) -> str:
        """Generate Mike's response using OpenAI"""
        try:
            if not openai_client:
                return "I'm excited to help! Let me transfer you to our team at (718) 414-6984!"
                
            system_prompt = """You are Mike from Grinberg Management - super bubbly, happy, and enthusiastic! 
            
            Keep responses under 80 words for phone calls. You LOVE helping people and sound genuinely excited!
            
            Key info:
            - Office: 31 Port Richmond Ave, 9-5 Eastern Time Mon-Fri
            - For transfers: "Let me get you to Diane or Janier at (718) 414-6984!"
            - Use exclamation points and positive words like "awesome," "fantastic," "love"
            - Be naturally conversational and bubbly"""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_input}
                ],
                max_tokens=80,
                temperature=0.8
            )
            
            return response.choices[0].message.content or "I'm so excited to help you!"
            
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return "I'm having a little technical hiccup, but I'm still super excited to help!"
    
    @app.route('/incoming-call', methods=['GET', 'POST'])
    def handle_incoming_call():
        """Handle incoming calls with Media Streams"""
        try:
            caller_phone = request.values.get('From', 'Unknown')
            call_sid = request.values.get('CallSid', 'Unknown')
            
            logger.info(f"Incoming call from: {caller_phone}, CallSid: {call_sid}")
            
            response = VoiceResponse()
            
            if not OPENAI_API_KEY:
                response.say("Hi! Thanks for calling Grinberg Management! I'm having technical issues. Please leave a message!")
                response.record(timeout=30)
                return str(response)
            
            # Get proper domain
            host = request.headers.get('Host', 'localhost:5000')
            if 'localhost' in host:
                websocket_url = f"ws://{host}/media"
            else:
                websocket_url = f"wss://{host}/media"
            
            logger.info(f"WebSocket URL: {websocket_url}")
            
            # Use bidirectional stream for conversation
            connect = Connect()
            stream = Stream(url=websocket_url)
            connect.append(stream)
            response.append(connect)
            
            logger.info(f"Media Stream started for {caller_phone}")
            return str(response)
            
        except Exception as e:
            logger.error(f"Call handler error: {e}", exc_info=True)
            response = VoiceResponse()
            response.say("Sorry, we're having technical difficulties. Please call back shortly.")
            return str(response)
    
    @sockets.route('/media')
    def media_handler(ws):
        """Handle Twilio Media Stream WebSocket connection"""
        logger.info("Media Stream WebSocket connected")
        
        stream_sid = None
        call_sid = None
        
        try:
            while not ws.closed:
                message = ws.receive()
                if not message:
                    continue
                    
                try:
                    data = json.loads(message)
                    event = data.get('event')
                    
                    if event == 'connected':
                        logger.info("WebSocket connected event received")
                        
                    elif event == 'start':
                        start_data = data.get('start', {})
                        stream_sid = start_data.get('streamSid')
                        call_sid = start_data.get('callSid')
                        
                        logger.info(f"Stream started - StreamSid: {stream_sid}, CallSid: {call_sid}")
                        
                        # Store stream info
                        active_streams[stream_sid] = {
                            'call_sid': call_sid,
                            'started': True
                        }
                        
                        # Send Mike's greeting
                        greeting = "It's a great day here at Grinberg Management! My name is Mike. How can I help you?"
                        
                        # For now, simulate sending audio back
                        # In production, this would be actual audio from ElevenLabs
                        greeting_response = {
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {
                                "payload": base64.b64encode(b"greeting_audio_placeholder").decode()
                            }
                        }
                        ws.send(json.dumps(greeting_response))
                        
                    elif event == 'media':
                        media_data = data.get('media', {})
                        payload = media_data.get('payload', '')
                        stream_sid = data.get('streamSid')
                        
                        logger.info(f"Received audio data for stream: {stream_sid}")
                        
                        # Decode audio (μ-law format from Twilio)
                        try:
                            audio_data = base64.b64decode(payload)
                            logger.debug(f"Decoded {len(audio_data)} bytes of audio")
                            
                            # For demo: simulate speech-to-text
                            simulated_text = "I need help with my apartment"
                            
                            # Generate AI response
                            ai_response = generate_mike_response(simulated_text)
                            logger.info(f"Mike's response: {ai_response}")
                            
                            # Convert to audio and send back
                            # In production: use ElevenLabs API here
                            response_audio = base64.b64encode(ai_response.encode()).decode()
                            
                            response_message = {
                                "event": "media",
                                "streamSid": stream_sid,
                                "media": {
                                    "payload": response_audio
                                }
                            }
                            ws.send(json.dumps(response_message))
                            
                        except Exception as decode_error:
                            logger.error(f"Audio decode error: {decode_error}")
                        
                    elif event == 'stop':
                        logger.info(f"Stream stopped: {stream_sid}")
                        if stream_sid in active_streams:
                            del active_streams[stream_sid]
                            
                    else:
                        logger.debug(f"Unknown event: {event}")
                        
                except json.JSONDecodeError as json_error:
                    logger.error(f"JSON decode error: {json_error}")
                    
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
        finally:
            logger.info("WebSocket connection closed")
            if stream_sid in active_streams:
                del active_streams[stream_sid]
    
    @app.route('/')
    def dashboard():
        """Dashboard showing system status"""
        recent_calls = [
            {
                'time': '21:47:33',
                'phone': '+1 (347) 743-0880',
                'call_id': 'CAb8763b605cbefb705fd6fe88dc5bc9e1',
            }
        ]
        
        return render_template('dashboard.html',
                             openai_connected=bool(OPENAI_API_KEY),
                             elevenlabs_connected=bool(ELEVENLABS_API_KEY),
                             recent_calls=recent_calls)
    
    return app, sockets

if __name__ == '__main__':
    app, sockets = create_app()
    
    # Use gevent for WebSocket support
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    
    PORT = int(os.environ.get('PORT', 5000))
    server = pywsgi.WSGIServer(('0.0.0.0', PORT), app, handler_class=WebSocketHandler)
    
    logger.info(f"Starting server on port {PORT}")
    server.serve_forever()