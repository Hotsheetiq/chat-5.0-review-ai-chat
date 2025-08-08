"""
Real-time Voice Routes for OpenAI Integration
Handles WebSocket connections, streaming audio, and real-time conversation modes
"""

from flask import request, jsonify
from flask_socketio import emit
import os
import json
import base64
import logging
import asyncio
from openai_realtime_integration import openai_assistant
from voice_activity_detection import vad_detector

logger = logging.getLogger(__name__)

def register_realtime_routes(app, socketio):
    """Register all real-time voice routes with the Flask app"""
    
    @app.route("/voice-mode/<mode>", methods=["POST"])
    def set_voice_mode(mode):
        """Switch between voice operation modes"""
        try:
            valid_modes = ["default", "live", "reasoning"]
            if mode not in valid_modes:
                return jsonify({"error": "Invalid mode", "valid_modes": valid_modes}), 400
            
            openai_assistant.current_mode = mode
            logger.info(f"Voice mode switched to: {mode}")
            
            return jsonify({
                "success": True,
                "mode": mode,
                "description": {
                    "default": "STT → OpenAI Chat (gpt-4o-mini) → ElevenLabs Streaming",
                    "live": "OpenAI Realtime API with Voice Activity Detection",
                    "reasoning": "Heavy reasoning with gpt-4.1/gpt-5.0 when needed"
                }[mode]
            })
            
        except Exception as e:
            logger.error(f"Mode switching error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/voice-status", methods=["GET"])
    def get_voice_status():
        """Get current voice assistant status"""
        try:
            status = openai_assistant.get_system_status()
            vad_status = vad_detector.get_status()
            
            return jsonify({
                "openai_status": status,
                "vad_status": vad_status,
                "system_ready": status["openai_connected"] and not status["processing"]
            })
            
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/start-realtime/<call_sid>", methods=["POST"])
    def start_realtime_session(call_sid):
        """Start OpenAI Realtime session for a specific call"""
        try:
            success = asyncio.run(openai_assistant.start_realtime_session(call_sid))
            
            if success:
                return jsonify({
                    "success": True,
                    "call_sid": call_sid,
                    "message": "Realtime session started",
                    "mode": "live"
                })
            else:
                return jsonify({
                    "error": "Failed to start realtime session",
                    "call_sid": call_sid
                }), 500
                
        except Exception as e:
            logger.error(f"Realtime session start error: {e}")
            return jsonify({"error": str(e)}), 500
    
    @app.route("/interrupt-response/<call_sid>", methods=["POST"])
    def handle_user_interruption(call_sid):
        """Handle user interruption during AI response"""
        try:
            asyncio.run(openai_assistant.handle_interruption(call_sid))
            
            return jsonify({
                "success": True,
                "message": "Response interrupted",
                "call_sid": call_sid
            })
            
        except Exception as e:
            logger.error(f"Interruption handling error: {e}")
            return jsonify({"error": str(e)}), 500
    
    # WebSocket events for real-time streaming
    @socketio.on('twilio_media')
    def handle_twilio_media(data):
        """Handle incoming audio from Twilio Media Streams"""
        try:
            call_sid = data.get('callSid')
            media_data = data.get('media', {})
            audio_payload = media_data.get('payload')
            
            if audio_payload and call_sid:
                # Decode audio data
                audio_data = base64.b64decode(audio_payload)
                
                # Process with VAD
                is_speaking, speech_ended = vad_detector.process_audio_chunk(audio_data)
                
                # Emit VAD status for monitoring
                emit('vad_status', {
                    'call_sid': call_sid,
                    'is_speaking': is_speaking,
                    'speech_ended': speech_ended
                })
                
                if openai_assistant.current_mode == "live":
                    # Send to OpenAI Realtime in live mode
                    asyncio.run(openai_assistant.handle_realtime_audio(audio_data, call_sid))
                
                if speech_ended:
                    # Trigger response generation
                    emit('speech_ended', {'call_sid': call_sid})
                    
        except Exception as e:
            logger.error(f"Media handling error: {e}")
            emit('error', {'message': str(e)})
    
    @socketio.on('audio_stream')
    def handle_audio_stream(data):
        """Handle continuous audio streaming"""
        try:
            call_sid = data.get('call_sid')
            audio_data = base64.b64decode(data.get('audio', ''))
            
            # Process audio in current mode
            if openai_assistant.current_mode == "live":
                asyncio.run(openai_assistant.handle_realtime_audio(audio_data, call_sid))
            else:
                # Accumulate audio for default mode processing
                pass
                
        except Exception as e:
            logger.error(f"Audio streaming error: {e}")
    
    @socketio.on('connect')
    def handle_websocket_connect():
        """Handle WebSocket connection"""
        logger.info("WebSocket client connected")
        emit('connected', {'status': 'Connected to voice assistant'})
    
    @socketio.on('disconnect')
    def handle_websocket_disconnect():
        """Handle WebSocket disconnection"""
        logger.info("WebSocket client disconnected")
    
    @app.route("/generate-streaming-audio/<call_sid>", methods=["GET"])
    def generate_streaming_audio(call_sid):
        """Generate streaming audio for real-time playback"""
        try:
            text = request.args.get('text', '')
            mode = request.args.get('mode', 'default')
            
            if not text:
                return "No text provided", 400
            
            # Use ElevenLabs Flash voice for lowest latency
            voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam voice optimized for real-time
            
            import requests
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
            
            payload = {
                "text": text,
                "model_id": "eleven_flash_v2",  # Fastest model for real-time
                "voice_settings": {
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                    "style": 0.2,
                    "use_speaker_boost": False
                },
                "output_format": "mp3_22050_32",
                "optimize_streaming_latency": True
            }
            
            headers = {
                "Accept": "audio/mpeg",
                "xi-api-key": os.environ.get("ELEVENLABS_API_KEY"),
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, stream=True)
            
            if response.status_code == 200:
                return response.content, 200, {'Content-Type': 'audio/mpeg'}
            else:
                logger.error(f"ElevenLabs error: {response.status_code}")
                return "Audio generation failed", 500
                
        except Exception as e:
            logger.error(f"Streaming audio error: {e}")
            return str(e), 500

    logger.info("Real-time voice routes registered successfully")