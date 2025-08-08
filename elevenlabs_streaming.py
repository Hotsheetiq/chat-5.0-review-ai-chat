"""
ElevenLabs Streaming TTS Integration
Real-time text-to-speech with Flash voices for ultra-low latency
"""

import os
import json
import logging
import asyncio
import websockets
import base64
import requests
from typing import Optional, AsyncGenerator
import tempfile
import time

logger = logging.getLogger(__name__)

class ElevenLabsStreaming:
    """ElevenLabs streaming TTS for real-time voice synthesis"""
    
    def __init__(self):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Use Flash voices for ultra-low latency
        self.flash_voices = {
            "chris": "pNInz6obpgDQGcFmaJgB",  # Professional American male (Flash compatible)
            "adam_flash": "pNInz6obpgDQGcFmaJgB",  # Fast professional voice
            "sam_flash": "yoZ06aMxZJJ28mfd3POQ"    # Warm American male (Flash)
        }
        
        self.current_voice = "chris"
        self.stream_active = False
        
        # Optimized settings for real-time streaming
        self.voice_settings = {
            "stability": 0.6,         # Reduced for faster processing
            "similarity_boost": 0.7,  # Balanced for speed and quality
            "style": 0.3,            # Moderate style for natural speech
            "use_speaker_boost": False # Disabled for consistent volume
        }

    async def stream_text_to_speech(self, text_tokens: AsyncGenerator[str, None], 
                                  call_sid: str) -> AsyncGenerator[bytes, None]:
        """Stream TTS audio as text tokens arrive from OpenAI"""
        try:
            self.stream_active = True
            buffer = ""
            sentence_endings = ['.', '!', '?', '\n']
            
            async for token in text_tokens:
                if not self.stream_active:
                    break
                    
                buffer += token
                
                # Generate audio when we have a complete sentence or clause
                if any(ending in buffer for ending in sentence_endings) or len(buffer) > 100:
                    if buffer.strip():
                        audio_data = await self.generate_speech_chunk(buffer.strip())
                        if audio_data:
                            yield audio_data
                        buffer = ""
                        
            # Generate final audio for remaining buffer
            if buffer.strip() and self.stream_active:
                audio_data = await self.generate_speech_chunk(buffer.strip())
                if audio_data:
                    yield audio_data
                    
        except Exception as e:
            logger.error(f"Streaming TTS error: {e}")
        finally:
            self.stream_active = False

    async def generate_speech_chunk(self, text: str) -> Optional[bytes]:
        """Generate audio for a text chunk using ElevenLabs"""
        try:
            if not self.api_key:
                logger.warning("ElevenLabs API key not available")
                return None
                
            voice_id = self.flash_voices.get(self.current_voice)
            if not voice_id:
                voice_id = self.flash_voices["chris"]  # Fallback
                
            url = f"{self.base_url}/text-to-speech/{voice_id}/stream"
            
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "model_id": "eleven_flash_v2",  # Flash model for ultra-low latency
                "voice_settings": self.voice_settings,
                "output_format": "mp3_22050_32",  # Optimized for real-time
                "optimize_streaming_latency": 4,   # Maximum streaming optimization
                "similar_to_request_id": None
            }
            
            # Make streaming request
            response = requests.post(url, headers=headers, json=data, stream=True)
            
            if response.status_code == 200:
                audio_chunks = b""
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        audio_chunks += chunk
                return audio_chunks
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Speech generation error: {e}")
            return None

    async def stream_complete_response(self, text: str) -> AsyncGenerator[bytes, None]:
        """Stream complete text as audio (non-token streaming)"""
        try:
            # Split text into chunks for streaming
            sentences = self.split_into_sentences(text)
            
            for sentence in sentences:
                if sentence.strip() and self.stream_active:
                    audio_data = await self.generate_speech_chunk(sentence)
                    if audio_data:
                        yield audio_data
                        
        except Exception as e:
            logger.error(f"Complete response streaming error: {e}")

    def split_into_sentences(self, text: str) -> list:
        """Split text into sentences for streaming"""
        import re
        # Split on sentence endings but keep them
        sentences = re.split(r'([.!?]+)', text)
        result = []
        
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i]
            if i + 1 < len(sentences):
                sentence += sentences[i + 1]
            if sentence.strip():
                result.append(sentence.strip())
                
        return result

    def stop_streaming(self):
        """Stop current streaming (for interruptions)"""
        logger.info("Stopping ElevenLabs streaming")
        self.stream_active = False

    def set_voice(self, voice_name: str):
        """Change the current voice"""
        if voice_name in self.flash_voices:
            self.current_voice = voice_name
            logger.info(f"Voice changed to: {voice_name}")
        else:
            logger.warning(f"Voice {voice_name} not available, using default")

    async def generate_quick_audio(self, text: str, voice_name: str = None) -> Optional[str]:
        """Generate audio quickly for immediate playback (non-streaming)"""
        try:
            voice_id = self.flash_voices.get(voice_name or self.current_voice)
            if not voice_id:
                voice_id = self.flash_voices["chris"]
                
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "model_id": "eleven_flash_v2",  # Ultra-fast Flash model
                "voice_settings": self.voice_settings,
                "output_format": "mp3_22050_32",
                "optimize_streaming_latency": 4
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                # Save to temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                    temp_file.write(response.content)
                    return temp_file.name
            else:
                logger.error(f"ElevenLabs quick audio error: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Quick audio generation error: {e}")
            return None

    def get_latency_settings(self) -> dict:
        """Get optimal settings for low latency"""
        return {
            "model": "eleven_flash_v2",
            "optimize_streaming_latency": 4,
            "output_format": "mp3_22050_32",
            "voice_settings": self.voice_settings
        }

# Global instance
streaming_tts = ElevenLabsStreaming()

async def handle_token_streaming(text_generator: AsyncGenerator[str, None], 
                               websocket, call_sid: str):
    """Handle real-time token streaming to TTS"""
    try:
        audio_stream = streaming_tts.stream_text_to_speech(text_generator, call_sid)
        
        async for audio_chunk in audio_stream:
            if audio_chunk:
                # Send audio chunk via WebSocket
                await websocket.send(json.dumps({
                    'event': 'audio_chunk',
                    'audio': base64.b64encode(audio_chunk).decode('utf-8'),
                    'call_sid': call_sid
                }))
                
    except Exception as e:
        logger.error(f"Token streaming error: {e}")

def create_instant_audio(text: str, voice_name: str = None) -> Optional[str]:
    """Create audio instantly for immediate use"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        audio_path = loop.run_until_complete(
            streaming_tts.generate_quick_audio(text, voice_name)
        )
        loop.close()
        return audio_path
    except Exception as e:
        logger.error(f"Instant audio error: {e}")
        return None