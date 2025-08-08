"""
Real-time audio streaming handler for WebSocket connections
Manages bidirectional audio streaming between Twilio and OpenAI/ElevenLabs
"""

import asyncio
import json
import base64
import logging
from typing import Optional, Dict, Any
import websockets
from flask import Flask
from flask_socketio import SocketIO, emit
import aiohttp

logger = logging.getLogger(__name__)

class StreamingAudioHandler:
    def __init__(self, app: Flask):
        self.app = app
        self.socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
        self.active_streams = {}  # call_sid -> stream_info
        
        # Register WebSocket handlers
        self.socketio.on_event('connect', self.handle_connect)
        self.socketio.on_event('disconnect', self.handle_disconnect)
        self.socketio.on_event('media', self.handle_media_stream)
        self.socketio.on_event('start', self.handle_stream_start)
        
    def handle_connect(self, auth):
        """Handle WebSocket connection from Twilio"""
        logger.info("WebSocket connected")
        emit('connected', {'status': 'Connected to streaming handler'})
        
    def handle_disconnect(self):
        """Handle WebSocket disconnection"""
        logger.info("WebSocket disconnected")
        
    def handle_stream_start(self, data):
        """Handle stream start event from Twilio"""
        try:
            call_sid = data.get('start', {}).get('callSid')
            stream_sid = data.get('start', {}).get('streamSid')
            
            if call_sid:
                self.active_streams[call_sid] = {
                    'stream_sid': stream_sid,
                    'started_at': asyncio.get_event_loop().time(),
                    'openai_connected': False,
                    'elevenlabs_connected': False
                }
                
                logger.info(f"Started audio stream for call {call_sid}")
                
                # Start OpenAI Realtime connection
                asyncio.create_task(self.connect_openai_realtime(call_sid))
                
        except Exception as e:
            logger.error(f"Stream start error: {e}")
    
    async def connect_openai_realtime(self, call_sid: str):
        """Establish OpenAI Realtime API connection for streaming"""
        try:
            from openai_realtime_integration import openai_assistant
            
            success = await openai_assistant.start_realtime_session(call_sid)
            if success and call_sid in self.active_streams:
                self.active_streams[call_sid]['openai_connected'] = True
                logger.info(f"OpenAI Realtime connected for {call_sid}")
            
        except Exception as e:
            logger.error(f"OpenAI Realtime connection error: {e}")
    
    def handle_media_stream(self, data):
        """Handle incoming audio data from Twilio"""
        try:
            media = data.get('media', {})
            call_sid = self.get_call_sid_from_stream(data)
            
            if call_sid and call_sid in self.active_streams:
                payload = media.get('payload')
                if payload:
                    # Decode audio data
                    audio_data = base64.b64decode(payload)
                    
                    # Process with VAD
                    from voice_activity_detection import vad_detector
                    is_speaking, speech_ended = vad_detector.process_audio_chunk(audio_data)
                    
                    if is_speaking:
                        # User is speaking - send to OpenAI Realtime
                        asyncio.create_task(self.send_audio_to_openai(call_sid, audio_data))
                    
                    if speech_ended:
                        # User finished speaking - trigger response
                        asyncio.create_task(self.trigger_ai_response(call_sid))
                        
        except Exception as e:
            logger.error(f"Media stream handling error: {e}")
    
    async def send_audio_to_openai(self, call_sid: str, audio_data: bytes):
        """Send audio data to OpenAI Realtime API"""
        try:
            from openai_realtime_integration import openai_assistant
            
            if self.active_streams.get(call_sid, {}).get('openai_connected'):
                await openai_assistant.handle_realtime_audio(audio_data, call_sid)
                
        except Exception as e:
            logger.error(f"OpenAI audio sending error: {e}")
    
    async def trigger_ai_response(self, call_sid: str):
        """Trigger AI response generation after user stops speaking"""
        try:
            from openai_realtime_integration import openai_assistant
            
            # In realtime mode, OpenAI will automatically respond
            # For default mode, we need to process the accumulated audio
            
            logger.info(f"AI response triggered for {call_sid}")
            
        except Exception as e:
            logger.error(f"AI response trigger error: {e}")
    
    async def stream_audio_to_twilio(self, call_sid: str, audio_data: bytes):
        """Stream audio response back to Twilio"""
        try:
            stream_info = self.active_streams.get(call_sid)
            if not stream_info:
                return
                
            # Encode audio for Twilio
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            media_message = {
                'event': 'media',
                'streamSid': stream_info['stream_sid'],
                'media': {
                    'payload': audio_base64
                }
            }
            
            # Send to Twilio via WebSocket
            self.socketio.emit('media', media_message)
            
        except Exception as e:
            logger.error(f"Audio streaming to Twilio error: {e}")
    
    def get_call_sid_from_stream(self, data: Dict) -> Optional[str]:
        """Extract call SID from stream data"""
        try:
            # Check various possible locations for call SID
            if 'start' in data:
                return data['start'].get('callSid')
            elif 'media' in data:
                return data['media'].get('callSid')
            else:
                # Find call SID from active streams
                stream_sid = data.get('streamSid')
                for call_sid, info in self.active_streams.items():
                    if info.get('stream_sid') == stream_sid:
                        return call_sid
                        
        except Exception as e:
            logger.error(f"Call SID extraction error: {e}")
            
        return None
    
    def get_stream_status(self) -> Dict[str, Any]:
        """Get current streaming status for dashboard"""
        active_count = len(self.active_streams)
        
        status = {
            'active_streams': active_count,
            'streams': {}
        }
        
        for call_sid, info in self.active_streams.items():
            status['streams'][call_sid] = {
                'duration': asyncio.get_event_loop().time() - info['started_at'],
                'openai_connected': info['openai_connected'],
                'elevenlabs_connected': info['elevenlabs_connected']
            }
        
        return status
    
    def cleanup_stream(self, call_sid: str):
        """Clean up resources for ended stream"""
        try:
            if call_sid in self.active_streams:
                del self.active_streams[call_sid]
                logger.info(f"Cleaned up stream for {call_sid}")
                
        except Exception as e:
            logger.error(f"Stream cleanup error: {e}")

# Global streaming handler instance
streaming_handler = None

def initialize_streaming_handler(app: Flask) -> StreamingAudioHandler:
    """Initialize streaming handler with Flask app"""
    global streaming_handler
    streaming_handler = StreamingAudioHandler(app)
    return streaming_handler