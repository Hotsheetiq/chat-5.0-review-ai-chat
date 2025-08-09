"""
ElevenLabs Streaming TTS Client
Handles streaming text-to-speech with low latency Flash voices
Supports both full streaming and sentence-chunk modes
"""

import os
import json
import logging
import asyncio
import websockets
import time
from collections import defaultdict
import requests

logger = logging.getLogger(__name__)

class ElevenLabsStreamingClient:
    def __init__(self):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ValueError("ELEVENLABS_API_KEY environment variable required")
            
        self.voice_id = "nPczCjzI2devNBz1zQrb"  # Flash voice for low latency
        self.active_sessions = {}
        self.audio_buffers = defaultdict(list)
        
        # Flash model settings for fastest response
        self.voice_settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
        
    def test_streaming(self):
        """Test if streaming capabilities are available"""
        try:
            # Test basic API connectivity
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key
            }
            response = requests.get("https://api.elevenlabs.io/v1/voices", headers=headers, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"ElevenLabs streaming test failed: {e}")
            return False
    
    async def start_streaming_session(self, call_sid):
        """Start streaming session for a call"""
        try:
            logger.info(f"🎤 Starting ElevenLabs streaming session for {call_sid}")
            
            # Initialize WebSocket connection to ElevenLabs
            ws_url = f"wss://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}/stream-input?model_id=eleven_flash_v2_5"
            
            headers = {
                "xi-api-key": self.api_key
            }
            
            websocket = await websockets.connect(ws_url, extra_headers=headers)
            
            # Send initial configuration
            config_message = {
                "text": " ",  # Start with space to initialize
                "voice_settings": self.voice_settings,
                "generation_config": {
                    "chunk_length_schedule": [120, 160, 250, 290]  # Optimized for low latency
                }
            }
            
            await websocket.send(json.dumps(config_message))
            
            self.active_sessions[call_sid] = {
                'websocket': websocket,
                'start_time': time.time(),
                'total_chars': 0,
                'chunks_sent': 0
            }
            
            # Start audio collection task
            asyncio.create_task(self.collect_audio_chunks(call_sid))
            
            logger.info(f"✅ ElevenLabs streaming session ready for {call_sid}")
            
        except Exception as e:
            logger.error(f"Failed to start ElevenLabs streaming session: {e}")
            raise
    
    async def send_token(self, call_sid, token):
        """Send individual token for full streaming mode"""
        try:
            if call_sid not in self.active_sessions:
                logger.warning(f"No active session for {call_sid}")
                return
                
            session = self.active_sessions[call_sid]
            websocket = session['websocket']
            
            # Send token immediately
            message = {
                "text": token,
                "try_trigger_generation": True
            }
            
            await websocket.send(json.dumps(message))
            session['total_chars'] += len(token)
            session['chunks_sent'] += 1
            
        except Exception as e:
            logger.error(f"Error sending token to ElevenLabs: {e}")
    
    async def synthesize_and_stream(self, call_sid, text):
        """Synthesize complete text chunk for sentence-chunk mode"""
        try:
            if call_sid not in self.active_sessions:
                await self.start_streaming_session(call_sid)
                
            session = self.active_sessions[call_sid]
            websocket = session['websocket']
            
            # Send complete text
            message = {
                "text": text,
                "try_trigger_generation": True
            }
            
            await websocket.send(json.dumps(message))
            session['total_chars'] += len(text)
            session['chunks_sent'] += 1
            
            logger.info(f"📝 Sent text to ElevenLabs: '{text[:50]}...' ({len(text)} chars)")
            
        except Exception as e:
            logger.error(f"Error synthesizing text: {e}")
    
    async def collect_audio_chunks(self, call_sid):
        """Collect audio chunks from ElevenLabs WebSocket"""
        try:
            session = self.active_sessions[call_sid]
            websocket = session['websocket']
            
            while call_sid in self.active_sessions:
                try:
                    # Receive audio chunks
                    response = await websocket.recv()
                    
                    if isinstance(response, bytes):
                        # Audio data received
                        self.audio_buffers[call_sid].append(response)
                        logger.debug(f"🔊 Received audio chunk for {call_sid}: {len(response)} bytes")
                    else:
                        # JSON message received
                        data = json.loads(response)
                        if 'audio' in data:
                            # Base64 encoded audio
                            import base64
                            audio_data = base64.b64decode(data['audio'])
                            self.audio_buffers[call_sid].append(audio_data)
                            logger.debug(f"🔊 Received base64 audio for {call_sid}: {len(audio_data)} bytes")
                            
                except websockets.exceptions.ConnectionClosed:
                    logger.info(f"ElevenLabs WebSocket closed for {call_sid}")
                    break
                except Exception as e:
                    logger.error(f"Error collecting audio chunks: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Audio collection task error: {e}")
    
    async def get_audio_chunk(self, call_sid):
        """Get next available audio chunk for playback"""
        try:
            if call_sid in self.audio_buffers and self.audio_buffers[call_sid]:
                # Return first available chunk
                return self.audio_buffers[call_sid].pop(0)
            return None
            
        except Exception as e:
            logger.error(f"Error getting audio chunk: {e}")
            return None
    
    async def finish_generation(self, call_sid):
        """Signal end of text input to complete generation"""
        try:
            if call_sid not in self.active_sessions:
                return
                
            session = self.active_sessions[call_sid]
            websocket = session['websocket']
            
            # Send end-of-stream signal
            end_message = {
                "text": ""
            }
            
            await websocket.send(json.dumps(end_message))
            logger.info(f"🏁 Finished text generation for {call_sid}")
            
        except Exception as e:
            logger.error(f"Error finishing generation: {e}")
    
    async def cleanup_session(self, call_sid):
        """Clean up streaming session resources"""
        try:
            if call_sid in self.active_sessions:
                session = self.active_sessions[call_sid]
                
                # Log session stats
                duration = time.time() - session['start_time']
                logger.info(f"📊 ElevenLabs session {call_sid}: {session['total_chars']} chars, "
                          f"{session['chunks_sent']} chunks, {duration:.1f}s")
                
                # Close WebSocket
                if 'websocket' in session:
                    await session['websocket'].close()
                
                del self.active_sessions[call_sid]
            
            # Clear audio buffer
            if call_sid in self.audio_buffers:
                del self.audio_buffers[call_sid]
                
            logger.info(f"🧹 Cleaned up ElevenLabs session for {call_sid}")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    def get_session_stats(self, call_sid):
        """Get current session statistics"""
        if call_sid not in self.active_sessions:
            return None
            
        session = self.active_sessions[call_sid]
        return {
            'active': True,
            'duration': time.time() - session['start_time'],
            'total_chars': session['total_chars'],
            'chunks_sent': session['chunks_sent'],
            'audio_buffer_size': len(self.audio_buffers.get(call_sid, []))
        }

# Global streaming client instance
streaming_tts_client = ElevenLabsStreamingClient()

def register_elevenlabs_routes(app):
    """Register ElevenLabs streaming routes"""
    
    @app.route('/tts-status/<call_sid>', methods=['GET'])
    def get_tts_status(call_sid):
        """Get TTS session status"""
        try:
            stats = streaming_tts_client.get_session_stats(call_sid)
            if stats:
                return jsonify(stats)
            else:
                return jsonify({'active': False})
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/test-tts-streaming', methods=['POST'])
    def test_tts_streaming():
        """Test TTS streaming capability"""
        try:
            available = streaming_tts_client.test_streaming()
            return jsonify({
                'available': available,
                'voice_id': streaming_tts_client.voice_id,
                'model': 'eleven_flash_v2_5'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    logger.info("🎤 ElevenLabs streaming routes registered")