"""
Real-time Voice Assistant Application
Integrates OpenAI Realtime API with ElevenLabs Streaming TTS
"""

import os
import json
import logging
import asyncio
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from twilio.twiml.voice_response import VoiceResponse, Connect
import threading
from datetime import datetime
import pytz

# Import our new streaming modules
from openai_realtime_integration import realtime_assistant, handle_realtime_conversation
from elevenlabs_streaming import streaming_tts, handle_token_streaming, create_instant_audio

# Import existing property management features
from rent_manager import RentManagerAPI
from address_matcher import AddressMatcher

logger = logging.getLogger(__name__)

class RealtimeVoiceApp:
    """Real-time voice assistant application"""
    
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        
        # Initialize property management systems (with error handling)
        try:
            self.rent_manager = RentManagerAPI({
                'username': os.environ.get('RENT_MANAGER_USERNAME'),
                'password': os.environ.get('RENT_MANAGER_PASSWORD'),
                'location_id': os.environ.get('RENT_MANAGER_LOCATION_ID'),
                'api_key': os.environ.get('RENT_MANAGER_API_KEY')
            })
        except Exception as e:
            logger.warning(f"RentManager initialization failed: {e}")
            self.rent_manager = None
            
        try:
            self.address_matcher = AddressMatcher(self.rent_manager)
        except Exception as e:
            logger.warning(f"AddressMatcher initialization failed: {e}")
            self.address_matcher = None
        
        # Call tracking
        self.active_calls = {}
        self.conversation_history = {}
        
        self.setup_routes()
        self.setup_socketio_handlers()

    def setup_routes(self):
        """Setup Flask routes for Twilio integration"""
        
        @self.app.route('/')
        def home():
            """Home page with system status"""
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Real-time Voice Assistant</title></head>
            <body style="font-family: Arial; margin: 40px; background: #1a1a1a; color: #fff;">
                <h1>🎙️ Real-time Voice Assistant</h1>
                <p><strong>System Status:</strong> <span style="color: #4CAF50;">Online</span></p>
                <p><strong>AI Engine:</strong> OpenAI Realtime API (GPT-4o-mini + GPT-4.1/5.0)</p>
                <p><strong>Voice Synthesis:</strong> ElevenLabs Flash TTS Streaming</p>
                <p><strong>Property Management:</strong> {"✓" if self.rent_manager else "⚠️"} Rent Manager Integration</p>
                <h3>Available Endpoints:</h3>
                <ul>
                    <li><a href="/dashboard" style="color: #4CAF50;">/dashboard</a> - Real-time monitoring dashboard</li>
                    <li><a href="/realtime-call" style="color: #4CAF50;">/realtime-call</a> - Twilio voice webhook</li>
                    <li><a href="/quick-response" style="color: #4CAF50;">/quick-response</a> - API for quick responses</li>
                </ul>
                <p><strong>Phone Number:</strong> (888) 641-1102 (if configured)</p>
                <p><em>Real-time streaming voice assistant with ultra-low latency</em></p>
            </body>
            </html>
            """
        
        @self.app.route('/realtime-call', methods=['GET', 'POST'])
        def handle_realtime_call():
            """Handle incoming calls with real-time streaming"""
            try:
                caller_phone = request.values.get('From', 'Unknown')
                call_sid = request.values.get('CallSid', 'Unknown')
                
                logger.info(f"Real-time call from: {caller_phone}, CallSid: {call_sid}")
                
                # Track the call
                self.active_calls[call_sid] = {
                    'phone': caller_phone,
                    'start_time': datetime.now(pytz.timezone('US/Eastern')),
                    'status': 'active'
                }
                
                response = VoiceResponse()
                
                # Check if APIs are available
                if not os.environ.get("OPENAI_API_KEY") or not os.environ.get("ELEVENLABS_API_KEY"):
                    response.say("Hi! Thanks for calling Grinberg Management. We're having technical issues. Please call back soon!")
                    return str(response)
                
                # Get WebSocket URL for real-time streaming
                host = request.headers.get('Host', 'localhost:5000')
                if 'localhost' in host:
                    ws_url = f"ws://{host}/realtime-stream/{call_sid}"
                else:
                    ws_url = f"wss://{host}/realtime-stream/{call_sid}"
                
                # Create initial greeting
                greeting = "Hi there! This is Chris from Grinberg Management! I'm so excited to help you today! What can I do for you?"
                
                # Generate initial greeting audio
                greeting_audio = create_instant_audio(greeting, "chris")
                if greeting_audio:
                    response.play(f"https://{host}/serve-audio/{os.path.basename(greeting_audio)}")
                else:
                    response.say(greeting, voice='Polly.Joanna-Neural')
                
                # Connect to real-time streaming
                connect = Connect()
                connect.stream(url=ws_url)
                response.append(connect)
                
                logger.info(f"Real-time streaming initiated: {ws_url}")
                return str(response)
                
            except Exception as e:
                logger.error(f"Real-time call error: {e}")
                response = VoiceResponse()
                response.say("I'm sorry, we're experiencing technical issues. Please try calling back.")
                return str(response)

        @self.app.route('/quick-response', methods=['POST'])
        def quick_response():
            """Handle quick non-streaming responses"""
            try:
                data = request.get_json()
                user_input = data.get('input', '')
                call_sid = data.get('call_sid', '')
                
                # Generate quick response
                from openai_realtime_integration import create_realtime_response
                response_text = create_realtime_response(user_input, call_sid)
                
                # Generate audio
                audio_path = create_instant_audio(response_text, "chris")
                
                return jsonify({
                    'text': response_text,
                    'audio_url': f"/serve-audio/{os.path.basename(audio_path)}" if audio_path else None,
                    'success': True
                })
                
            except Exception as e:
                logger.error(f"Quick response error: {e}")
                return jsonify({'error': str(e), 'success': False})

        @self.app.route('/serve-audio/<filename>')
        def serve_audio(filename):
            """Serve generated audio files"""
            try:
                import tempfile
                audio_path = os.path.join(tempfile.gettempdir(), filename)
                
                if os.path.exists(audio_path):
                    from flask import send_file
                    return send_file(audio_path, mimetype='audio/mpeg')
                else:
                    return "Audio file not found", 404
                    
            except Exception as e:
                logger.error(f"Audio serving error: {e}")
                return "Error serving audio", 500

        @self.app.route('/call-status/<call_sid>')
        def call_status(call_sid):
            """Get status of a specific call"""
            call_info = self.active_calls.get(call_sid)
            if call_info:
                return jsonify({
                    'call_sid': call_sid,
                    'phone': call_info['phone'],
                    'status': call_info['status'],
                    'start_time': call_info['start_time'].isoformat(),
                    'conversation_length': len(self.conversation_history.get(call_sid, []))
                })
            else:
                return jsonify({'error': 'Call not found'}), 404

        @self.app.route('/status')
        def status():
            """API status endpoint"""
            return jsonify({
                'status': 'online',
                'ai_engine': 'OpenAI Realtime API',
                'tts_engine': 'ElevenLabs Flash',
                'active_calls': len(self.active_calls),
                'openai_available': bool(os.environ.get("OPENAI_API_KEY")),
                'elevenlabs_available': bool(os.environ.get("ELEVENLABS_API_KEY")),
                'rent_manager_available': self.rent_manager is not None
            })

        @self.app.route('/dashboard')
        def dashboard():
            """Real-time voice assistant dashboard"""
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Real-time Voice Assistant Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }
                    .container { max-width: 1200px; margin: 0 auto; }
                    .header { text-align: center; margin-bottom: 30px; }
                    .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                    .status-card { background: #2a2a2a; padding: 20px; border-radius: 8px; border: 1px solid #444; }
                    .status-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #4CAF50; }
                    .status-value { font-size: 24px; font-weight: bold; color: #fff; }
                    .call-log { background: #2a2a2a; padding: 20px; border-radius: 8px; margin-top: 20px; }
                    .call-entry { padding: 10px; border-bottom: 1px solid #444; }
                    .live-indicator { color: #4CAF50; font-weight: bold; }
                </style>
                <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎙️ Real-time Voice Assistant Dashboard</h1>
                        <p>OpenAI Realtime API + ElevenLabs Streaming TTS</p>
                    </div>
                    
                    <div class="status-grid">
                        <div class="status-card">
                            <div class="status-title">System Status</div>
                            <div class="status-value" id="system-status">Initializing...</div>
                        </div>
                        
                        <div class="status-card">
                            <div class="status-title">Active Calls</div>
                            <div class="status-value" id="active-calls">0</div>
                        </div>
                        
                        <div class="status-card">
                            <div class="status-title">Response Model</div>
                            <div class="status-value" id="ai-model">GPT-4o-mini</div>
                        </div>
                        
                        <div class="status-card">
                            <div class="status-title">Voice Model</div>
                            <div class="status-value" id="tts-model">ElevenLabs Flash</div>
                        </div>
                    </div>
                    
                    <div class="call-log">
                        <h3>Recent Call Activity</h3>
                        <div id="call-log-entries">
                            <div class="call-entry">Real-time voice assistant ready for calls...</div>
                        </div>
                    </div>
                </div>
                
                <script>
                    const socket = io();
                    
                    socket.on('connect', function() {
                        console.log('Connected to real-time dashboard');
                        document.getElementById('system-status').textContent = 'Online';
                        document.getElementById('system-status').style.color = '#4CAF50';
                    });
                    
                    socket.on('call_update', function(data) {
                        document.getElementById('active-calls').textContent = data.active_calls;
                        
                        const logEntries = document.getElementById('call-log-entries');
                        const entry = document.createElement('div');
                        entry.className = 'call-entry';
                        entry.innerHTML = `<span class="live-indicator">LIVE</span> ${data.message}`;
                        logEntries.insertBefore(entry, logEntries.firstChild);
                        
                        // Keep only last 10 entries
                        while (logEntries.children.length > 10) {
                            logEntries.removeChild(logEntries.lastChild);
                        }
                    });
                    
                    socket.on('model_update', function(data) {
                        document.getElementById('ai-model').textContent = data.model;
                    });
                    
                    // Update status every 30 seconds
                    setInterval(() => {
                        socket.emit('request_status');
                    }, 30000);
                </script>
            </body>
            </html>
            """

    def setup_socketio_handlers(self):
        """Setup SocketIO handlers for real-time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info("Dashboard client connected")
            emit('status', {'message': 'Real-time voice assistant online'})

        @self.socketio.on('request_status')
        def handle_status_request():
            emit('call_update', {
                'active_calls': len(self.active_calls),
                'message': f'System operational - {len(self.active_calls)} active calls'
            })

        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info("Dashboard client disconnected")

    async def handle_streaming_websocket(self, websocket, path):
        """Handle WebSocket connections for real-time streaming"""
        try:
            # Extract call_sid from path
            call_sid = path.split('/')[-1]
            logger.info(f"WebSocket connection for call: {call_sid}")
            
            # Handle the real-time conversation
            await handle_realtime_conversation(websocket, call_sid)
            
        except Exception as e:
            logger.error(f"WebSocket handling error: {e}")
        finally:
            # Cleanup
            if call_sid in self.active_calls:
                self.active_calls[call_sid]['status'] = 'ended'

    def run(self, host='0.0.0.0', port=5000, debug=False):
        """Run the real-time voice assistant application"""
        logger.info("Starting Real-time Voice Assistant with OpenAI + ElevenLabs")
        logger.info(f"OpenAI API Key: {'✓' if os.environ.get('OPENAI_API_KEY') else '✗'}")
        logger.info(f"ElevenLabs API Key: {'✓' if os.environ.get('ELEVENLABS_API_KEY') else '✗'}")
        
        self.socketio.run(self.app, host=host, port=port, debug=debug, 
                         allow_unsafe_werkzeug=True, use_reloader=False, log_output=False)

def create_app():
    """Create and return the Flask app for deployment"""
    voice_app = RealtimeVoiceApp()
    return voice_app.app

# For direct execution
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create and run the app
    app = RealtimeVoiceApp()
    app.run(debug=True)