"""
Twilio Media Streams Handler - Full Streaming Mode
Implements sub-1s streaming pipeline: STT → OpenAI → ElevenLabs → Twilio
Runtime mode selection: Full Streaming vs Sentence-Chunk Interim
"""

import os
import json
import base64
import logging
import asyncio
import websockets
import time
from datetime import datetime
import pytz
from flask import Flask, request, jsonify
from flask_sockets import Sockets
import gevent
from geventwebsocket.handler import WebSocketHandler
from openai_conversation_manager import conversation_manager
from elevenlabs_streaming import streaming_tts_client

logger = logging.getLogger(__name__)

class TwilioMediaStreamHandler:
    def __init__(self):
        self.active_streams = {}
        self.session_facts = {}
        self.conversation_histories = {}
        self.timing_data = {}
        
        # Runtime mode selection
        self.streaming_mode = "full"  # "full" or "sentence-chunk"
        
        # Grok usage guard
        self.grok_guard_active = True
        
    def detect_grok_usage(self, context):
        """Runtime guard to detect any Grok usage"""
        if any(term in str(context).lower() for term in ['grok', 'xai', 'x.ai']):
            logger.error("🚨 GROK USAGE DETECTED - STOPPING")
            raise Exception("Grok usage detected — migrate to OpenAI.")
    
    def get_current_mode(self):
        """Auto-select fastest working mode"""
        try:
            # Try full streaming first (fastest)
            if self.test_full_streaming_available():
                return "full_streaming"
            else:
                # Fallback to sentence-chunk interim
                return "sentence_chunk"
        except Exception as e:
            logger.warning(f"Mode detection failed, using sentence-chunk: {e}")
            return "sentence_chunk"
    
    def test_full_streaming_available(self):
        """Test if all components for full streaming are available"""
        try:
            # Check OpenAI streaming capability
            conversation_manager.test_streaming()
            # Check ElevenLabs streaming capability  
            streaming_tts_client.test_streaming()
            return True
        except Exception:
            return False
    
    async def handle_media_stream(self, websocket, path):
        """Handle incoming Twilio Media Stream WebSocket connection"""
        call_sid = None
        stream_start_time = time.time()
        
        try:
            logger.info("📞 New Twilio Media Stream connection established")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    event_type = data.get('event')
                    
                    if event_type == 'connected':
                        logger.info("🔗 Twilio Media Stream connected")
                        
                    elif event_type == 'start':
                        call_sid = data['start']['callSid']
                        logger.info(f"▶️ Media stream started for call: {call_sid}")
                        
                        # Initialize session
                        self.active_streams[call_sid] = {
                            'websocket': websocket,
                            'start_time': time.time(),
                            'audio_buffer': b'',
                            'last_activity': time.time()
                        }
                        self.session_facts[call_sid] = {}
                        self.conversation_histories[call_sid] = []
                        
                        # Auto-select mode at runtime
                        selected_mode = self.get_current_mode()
                        logger.info(f"🚀 Selected mode: {selected_mode}")
                        
                        if selected_mode == "full_streaming":
                            await self.start_full_streaming_pipeline(call_sid)
                        else:
                            await self.start_sentence_chunk_pipeline(call_sid)
                            
                    elif event_type == 'media':
                        if call_sid and call_sid in self.active_streams:
                            await self.process_audio_chunk(call_sid, data['media'])
                            
                    elif event_type == 'stop':
                        logger.info(f"⏹️ Media stream stopped for call: {call_sid}")
                        await self.cleanup_stream(call_sid)
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON received from Twilio")
                except Exception as e:
                    logger.error(f"Error processing media stream message: {e}")
                    
        except Exception as e:
            logger.error(f"Media stream handler error: {e}")
        finally:
            if call_sid:
                await self.cleanup_stream(call_sid)
    
    async def start_full_streaming_pipeline(self, call_sid):
        """Start full streaming mode: STT → OpenAI → ElevenLabs → Twilio (target <1s)"""
        logger.info(f"🚀 Starting FULL STREAMING mode for {call_sid}")
        
        # Initialize streaming components
        await conversation_manager.start_streaming_session(call_sid)
        await streaming_tts_client.start_streaming_session(call_sid)
        
        # Set up real-time pipeline
        self.active_streams[call_sid]['pipeline'] = 'full_streaming'
        self.active_streams[call_sid]['target_latency'] = 1.0  # <1s target
        
    async def start_sentence_chunk_pipeline(self, call_sid):
        """Start sentence-chunk mode: buffer by sentence, stream each (target <1.5s)"""
        logger.info(f"🔄 Starting SENTENCE-CHUNK mode for {call_sid}")
        
        self.active_streams[call_sid]['pipeline'] = 'sentence_chunk'
        self.active_streams[call_sid]['target_latency'] = 1.5  # <1.5s target
        self.active_streams[call_sid]['sentence_buffer'] = ""
        
    async def process_audio_chunk(self, call_sid, media_data):
        """Process incoming audio chunk based on current pipeline mode"""
        chunk_start = time.time()
        
        try:
            # Decode Twilio audio (mulaw, base64)
            audio_payload = base64.b64decode(media_data['payload'])
            
            # Add to buffer
            stream_info = self.active_streams[call_sid]
            stream_info['audio_buffer'] += audio_payload
            stream_info['last_activity'] = time.time()
            
            # Check if we have enough audio for processing (e.g., 160ms chunks)
            if len(stream_info['audio_buffer']) >= 1280:  # 160ms at 8kHz
                audio_chunk = stream_info['audio_buffer'][:1280]
                stream_info['audio_buffer'] = stream_info['audio_buffer'][1280:]
                
                if stream_info['pipeline'] == 'full_streaming':
                    await self.process_full_streaming(call_sid, audio_chunk, chunk_start)
                else:
                    await self.process_sentence_chunk(call_sid, audio_chunk, chunk_start)
                    
        except Exception as e:
            logger.error(f"Audio chunk processing error: {e}")
    
    async def process_full_streaming(self, call_sid, audio_chunk, start_time):
        """Full streaming: immediate token-by-token forwarding"""
        try:
            # STT with N-best hypotheses for accuracy
            stt_start = time.time()
            transcription_results = await self.perform_stt_with_nbest(audio_chunk)
            stt_time = time.time() - stt_start
            
            if not transcription_results:
                return
                
            # Select best hypothesis (check for emergency keywords in alternates)
            selected_text = self.select_best_hypothesis(transcription_results)
            
            if not selected_text.strip():
                return
                
            # Log STT timing
            self.log_timing(call_sid, "stt_ms", stt_time * 1000)
            
            # Guard against Grok usage
            self.detect_grok_usage(selected_text)
            
            # OpenAI streaming with memory injection
            openai_start = time.time()
            
            # Inject session facts into context
            enhanced_context = self.build_context_with_facts(call_sid, selected_text)
            
            # Stream OpenAI tokens directly to ElevenLabs
            first_token_time = None
            async for token in conversation_manager.stream_response(call_sid, enhanced_context):
                if first_token_time is None:
                    first_token_time = time.time()
                    self.log_timing(call_sid, "first_token_ms", (first_token_time - openai_start) * 1000)
                
                # Forward token immediately to ElevenLabs streaming
                await streaming_tts_client.send_token(call_sid, token)
            
            # Start audio playback as soon as we have enough buffered
            audio_start = time.time()
            await self.start_audio_playback(call_sid)
            first_audio_time = time.time() - start_time
            
            self.log_timing(call_sid, "first_audio_ms", first_audio_time * 1000)
            
            # Update session facts
            self.update_session_facts(call_sid, selected_text)
            
        except Exception as e:
            if "Grok usage detected" in str(e):
                raise
            logger.error(f"Full streaming processing error: {e}")
    
    async def process_sentence_chunk(self, call_sid, audio_chunk, start_time):
        """Sentence-chunk mode: buffer sentences, stream each immediately"""
        try:
            # STT processing
            stt_start = time.time()
            transcription_results = await self.perform_stt_with_nbest(audio_chunk)
            stt_time = time.time() - stt_start
            
            if not transcription_results:
                return
                
            selected_text = self.select_best_hypothesis(transcription_results)
            if not selected_text.strip():
                return
                
            self.log_timing(call_sid, "stt_ms", stt_time * 1000)
            
            # Guard against Grok usage
            self.detect_grok_usage(selected_text)
            
            # Add to sentence buffer
            stream_info = self.active_streams[call_sid]
            stream_info['sentence_buffer'] += selected_text + " "
            
            # Check for sentence completion
            if any(punct in selected_text for punct in ['.', '?', '!']):
                complete_sentence = stream_info['sentence_buffer'].strip()
                stream_info['sentence_buffer'] = ""
                
                # Process complete sentence
                await self.process_complete_sentence(call_sid, complete_sentence, start_time)
                
        except Exception as e:
            if "Grok usage detected" in str(e):
                raise
            logger.error(f"Sentence chunk processing error: {e}")
    
    async def process_complete_sentence(self, call_sid, sentence, start_time):
        """Process a complete sentence in sentence-chunk mode"""
        try:
            openai_start = time.time()
            
            # Build context with session facts
            enhanced_context = self.build_context_with_facts(call_sid, sentence)
            
            # Get OpenAI response (streaming)
            response_text = ""
            first_token_time = None
            
            async for token in conversation_manager.stream_response(call_sid, enhanced_context):
                if first_token_time is None:
                    first_token_time = time.time()
                    self.log_timing(call_sid, "first_token_ms", (first_token_time - openai_start) * 1000)
                response_text += token
                
                # Check for sentence completion in response
                if any(punct in token for punct in ['.', '?', '!']):
                    # Send completed sentence to ElevenLabs immediately
                    audio_start = time.time()
                    await streaming_tts_client.synthesize_and_stream(call_sid, response_text)
                    
                    # Start playback
                    await self.start_audio_playback(call_sid)
                    first_audio_time = time.time() - start_time
                    self.log_timing(call_sid, "first_audio_ms", first_audio_time * 1000)
                    
                    response_text = ""  # Reset for next sentence
            
            # Send any remaining text
            if response_text.strip():
                await streaming_tts_client.synthesize_and_stream(call_sid, response_text)
                await self.start_audio_playback(call_sid)
            
            # Update session facts
            self.update_session_facts(call_sid, sentence)
            
        except Exception as e:
            logger.error(f"Complete sentence processing error: {e}")
    
    async def perform_stt_with_nbest(self, audio_chunk):
        """Perform STT with N-best hypotheses for accuracy + emergency detection"""
        try:
            # Use OpenAI Whisper with multiple hypotheses
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            
            # Convert audio chunk to appropriate format for Whisper
            # Note: This is a simplified example - real implementation would need proper audio format conversion
            
            # For now, return mock structure - real implementation would call Whisper API
            return [
                {"text": "sample transcription", "confidence": 0.9},
                {"text": "alternate transcription", "confidence": 0.7},
                {"text": "emergency transcription", "confidence": 0.6}
            ]
            
        except Exception as e:
            logger.error(f"STT N-best error: {e}")
            return []
    
    def select_best_hypothesis(self, hypotheses):
        """Select best hypothesis, prioritizing emergency keywords in alternates"""
        if not hypotheses:
            return ""
            
        emergency_keywords = ["no heat", "flooding", "clogged toilet", "sewer backup", "fire"]
        
        # Check alternates for emergency keywords first
        for hypothesis in hypotheses[1:]:  # Skip top hypothesis, check alternates
            text = hypothesis.get("text", "").lower()
            if any(keyword in text for keyword in emergency_keywords):
                logger.info(f"🚨 Emergency keyword detected in alternate: {text}")
                return hypothesis.get("text", "")
        
        # Return top hypothesis if no emergency in alternates
        return hypotheses[0].get("text", "")
    
    def build_context_with_facts(self, call_sid, user_input):
        """Build context with session facts injection"""
        facts = self.session_facts.get(call_sid, {})
        
        # Build known facts string
        known_facts = []
        if facts.get('unitNumber'):
            known_facts.append(f"Unit={facts['unitNumber']}")
        if facts.get('reportedIssue'):
            known_facts.append(f"Issue={facts['reportedIssue']}")
        if facts.get('callbackName'):
            known_facts.append(f"Callback={facts['callbackName']}")
        if facts.get('callbackNumber'):
            known_facts.append(f"Number={facts['callbackNumber']}")
            
        facts_context = f"Known facts: {', '.join(known_facts) if known_facts else 'none yet'}"
        
        return {
            'user_input': user_input,
            'facts_context': facts_context,
            'conversation_history': self.conversation_histories.get(call_sid, [])[-10:]  # Last 10 turns
        }
    
    def update_session_facts(self, call_sid, text):
        """Extract and update session facts from user input"""
        if call_sid not in self.session_facts:
            self.session_facts[call_sid] = {}
            
        facts = self.session_facts[call_sid]
        text_lower = text.lower()
        
        # Extract unit number
        import re
        unit_match = re.search(r'unit\s*(\w+)|apartment\s*(\w+)', text_lower)
        if unit_match:
            facts['unitNumber'] = unit_match.group(1) or unit_match.group(2)
        
        # Extract issue type
        if any(word in text_lower for word in ['heat', 'heating', 'hot', 'cold']):
            facts['reportedIssue'] = 'Heating'
        elif any(word in text_lower for word in ['water', 'leak', 'plumbing']):
            facts['reportedIssue'] = 'Plumbing'
        elif any(word in text_lower for word in ['electric', 'electrical', 'power']):
            facts['reportedIssue'] = 'Electrical'
        elif any(word in text_lower for word in ['pest', 'roach', 'bug']):
            facts['reportedIssue'] = 'Pest'
            
        # Extract phone numbers
        phone_match = re.search(r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})', text)
        if phone_match:
            facts['callbackNumber'] = phone_match.group(1)
    
    async def start_audio_playback(self, call_sid):
        """Start audio playback through Twilio Media Stream"""
        try:
            if call_sid not in self.active_streams:
                return
                
            websocket = self.active_streams[call_sid]['websocket']
            
            # Get audio from ElevenLabs streaming buffer
            audio_data = await streaming_tts_client.get_audio_chunk(call_sid)
            
            if audio_data:
                # Encode for Twilio (base64 mulaw)
                encoded_audio = base64.b64encode(audio_data).decode('utf-8')
                
                # Send to Twilio Media Stream
                media_message = {
                    "event": "media",
                    "streamSid": call_sid,
                    "media": {
                        "payload": encoded_audio
                    }
                }
                
                await websocket.send(json.dumps(media_message))
                
        except Exception as e:
            logger.error(f"Audio playback error: {e}")
    
    def log_timing(self, call_sid, metric, value_ms):
        """Log timing metrics for performance monitoring"""
        if call_sid not in self.timing_data:
            self.timing_data[call_sid] = {}
            
        self.timing_data[call_sid][metric] = value_ms
        
        # Log critical metrics
        if metric == "first_audio_ms":
            target = self.active_streams[call_sid].get('target_latency', 1.0) * 1000
            status = "✅" if value_ms < target else "⚠️"
            logger.info(f"{status} {metric}: {value_ms:.1f}ms (target: <{target}ms)")
    
    async def cleanup_stream(self, call_sid):
        """Clean up resources for ended stream"""
        try:
            if call_sid in self.active_streams:
                # Log final timing summary
                timing = self.timing_data.get(call_sid, {})
                logger.info(f"📊 Call {call_sid} timing summary: {timing}")
                
                # Cleanup resources
                await conversation_manager.cleanup_session(call_sid)
                await streaming_tts_client.cleanup_session(call_sid)
                
                del self.active_streams[call_sid]
                
            if call_sid in self.timing_data:
                del self.timing_data[call_sid]
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Global handler instance
media_stream_handler = TwilioMediaStreamHandler()

def register_media_stream_routes(app):
    """Register media stream routes with Flask app"""
    sockets = Sockets(app)
    
    @sockets.route('/twilio-media')
    def twilio_media_websocket(ws):
        """WebSocket endpoint for Twilio Media Streams"""
        async def handler():
            await media_stream_handler.handle_media_stream(ws, '/twilio-media')
            
        # Run async handler
        import asyncio
        asyncio.run(handler())
    
    @app.route('/start-media-stream/<call_sid>', methods=['POST'])
    def start_media_stream(call_sid):
        """Start media stream for call"""
        try:
            # Generate TwiML for Twilio Media Stream
            host = request.headers.get('Host', 'localhost:5000')
            if host.startswith('0.0.0.0'):
                host = f"{os.environ.get('REPL_SLUG', 'maintenancelinker')}.{os.environ.get('REPL_OWNER', 'brokeropenhouse')}.repl.co"
            
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Connect>
                    <Stream url="wss://{host}/twilio-media?callSid={call_sid}" />
                </Connect>
            </Response>"""
            
            logger.info(f"🎯 Media stream TwiML generated for {call_sid}")
            return twiml, 200, {'Content-Type': 'application/xml'}
            
        except Exception as e:
            logger.error(f"Media stream start error: {e}")
            return str(e), 500
    
    @app.route('/stream-status/<call_sid>', methods=['GET'])
    def get_stream_status(call_sid):
        """Get current stream status and timing"""
        try:
            if call_sid in media_stream_handler.active_streams:
                stream_info = media_stream_handler.active_streams[call_sid]
                timing_info = media_stream_handler.timing_data.get(call_sid, {})
                
                return jsonify({
                    'active': True,
                    'pipeline': stream_info.get('pipeline'),
                    'target_latency_ms': stream_info.get('target_latency', 1.0) * 1000,
                    'timing': timing_info,
                    'session_facts': media_stream_handler.session_facts.get(call_sid, {})
                })
            else:
                return jsonify({'active': False})
                
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    logger.info("📡 Twilio Media Stream routes registered")