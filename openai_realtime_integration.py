"""
OpenAI Real-Time Voice Assistant Integration
Supports three operational modes:
1. Default: STT → OpenAI Chat (gpt-4o-mini) → ElevenLabs Streaming
2. Live/Interruptible: OpenAI Realtime API with VAD
3. Heavy Reasoning: Temporary switch to gpt-4.1/gpt-5.0
"""

import os
import json
import time
import logging
import asyncio
import websockets
import base64
from typing import Optional, Dict, Any, AsyncGenerator
from openai import OpenAI
import aiohttp

logger = logging.getLogger(__name__)

class OpenAIRealtimeAssistant:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.realtime_ws = None
        self.current_mode = "default"  # default, live, reasoning
        self.conversation_context = []
        self.is_processing = False
        self.user_speaking = False
        
        # Model configuration
        self.models = {
            "default": "gpt-4o-mini",
            "live": "gpt-4o-realtime-preview",
            "reasoning": "gpt-4o"  # Will upgrade to gpt-4.1/gpt-5.0 when available
        }
        
        # ElevenLabs streaming configuration
        self.elevenlabs_voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam voice
        self.elevenlabs_api_key = os.environ.get("ELEVENLABS_API_KEY")
        
    async def detect_complexity(self, user_input: str) -> str:
        """Detect if user input requires heavy reasoning"""
        reasoning_keywords = [
            "analyze", "explain", "complex", "detailed", "comprehensive",
            "calculate", "compare", "evaluate", "research", "investigate"
        ]
        
        if any(keyword in user_input.lower() for keyword in reasoning_keywords):
            return "reasoning"
        elif len(user_input.split()) > 20:  # Long queries might need reasoning
            return "reasoning"
        else:
            return "default"
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """Convert audio to text using OpenAI Whisper"""
        try:
            # Save audio data temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # Transcribe with Whisper
                with open(temp_file.name, "rb") as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                
                # Clean up temp file
                os.unlink(temp_file.name)
                return transcript.strip()
                
        except Exception as e:
            logger.error(f"Speech transcription error: {e}")
            return ""
    
    async def generate_streaming_response(self, messages: list, mode: str = "default") -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI Chat API"""
        try:
            model = self.models[mode]
            logger.info(f"Generating {mode} response with {model}")
            
            # Stream response from OpenAI
            stream = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                max_tokens=150 if mode == "default" else 300,
                temperature=0.7
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield f"I encountered an issue processing that. How can I help you?"
    
    async def stream_to_elevenlabs(self, text_stream: AsyncGenerator[str, None], call_sid: str) -> str:
        """Stream text chunks to ElevenLabs for real-time audio generation"""
        try:
            full_text = ""
            text_buffer = ""
            
            async for chunk in text_stream:
                full_text += chunk
                text_buffer += chunk
                
                # Send complete sentences to ElevenLabs for better audio flow
                if any(punct in text_buffer for punct in ['.', '!', '?', ';']) or len(text_buffer) > 50:
                    await self._generate_audio_chunk(text_buffer.strip(), call_sid)
                    text_buffer = ""
            
            # Send remaining text
            if text_buffer.strip():
                await self._generate_audio_chunk(text_buffer.strip(), call_sid)
            
            return full_text
            
        except Exception as e:
            logger.error(f"ElevenLabs streaming error: {e}")
            return full_text or "I'm here to help."
    
    async def _generate_audio_chunk(self, text: str, call_sid: str):
        """Generate audio chunk with ElevenLabs streaming"""
        if not text.strip():
            return
            
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.elevenlabs_voice_id}/stream"
            
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2_5",  # Fastest model
                "voice_settings": {
                    "stability": 0.75,
                    "similarity_boost": 0.75,
                    "style": 0.2,
                    "use_speaker_boost": False
                },
                "output_format": "mp3_22050_32",
                "optimize_streaming_latency": True
            }
            
            headers = {
                "Accept": "application/json",
                "xi-api-key": self.elevenlabs_api_key,
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        # Stream audio data as it arrives
                        async for chunk in response.content.iter_chunked(1024):
                            # TODO: Stream to Twilio WebSocket or save for immediate playback
                            pass
                    else:
                        logger.error(f"ElevenLabs API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Audio chunk generation error: {e}")
    
    async def start_realtime_session(self, call_sid: str):
        """Start OpenAI Realtime API session for live/interruptible calls"""
        try:
            # WebSocket connection to OpenAI Realtime API
            uri = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview"
            headers = {
                "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}",
                "OpenAI-Beta": "realtime=v1"
            }
            
            self.realtime_ws = await websockets.connect(uri, extra_headers=headers)
            logger.info(f"Started realtime session for {call_sid}")
            
            # Configure session
            await self._configure_realtime_session()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to start realtime session: {e}")
            return False
    
    async def _configure_realtime_session(self):
        """Configure OpenAI Realtime API session"""
        config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """You are Chris, a friendly property management assistant for Grinberg Management. 
                You help tenants with maintenance requests, general inquiries, and property information. 
                Keep responses concise and helpful. When creating service tickets, get the tenant's address and issue details.""",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500
                },
                "tools": [],
                "tool_choice": "auto",
                "temperature": 0.7,
                "max_response_output_tokens": 150
            }
        }
        
        await self.realtime_ws.send(json.dumps(config))
    
    async def handle_realtime_audio(self, audio_data: bytes, call_sid: str):
        """Handle incoming audio in realtime mode"""
        if not self.realtime_ws:
            return
            
        try:
            # Convert audio to base64 and send to OpenAI
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            message = {
                "type": "input_audio_buffer.append",
                "audio": audio_base64
            }
            
            await self.realtime_ws.send(json.dumps(message))
            
        except Exception as e:
            logger.error(f"Realtime audio handling error: {e}")
    
    async def process_default_mode(self, user_input: str, conversation_history: list, call_sid: str) -> str:
        """Process conversation in default streaming mode"""
        try:
            # Detect if we need reasoning mode
            detected_mode = await self.detect_complexity(user_input)
            
            # Build conversation context
            messages = [
                {"role": "system", "content": """You are Chris, a friendly property management assistant for Grinberg Management. 
                You help tenants with maintenance requests, general inquiries, and property information. 
                Keep responses concise, helpful, and under 30 words for fast processing."""}
            ]
            
            # Add conversation history
            for msg in conversation_history[-5:]:  # Last 5 messages for context
                if msg.get('speaker') == 'Caller':
                    messages.append({"role": "user", "content": msg.get('message', '')})
                elif msg.get('speaker') == 'Chris':
                    messages.append({"role": "assistant", "content": msg.get('message', '')})
            
            # Add current user input
            messages.append({"role": "user", "content": user_input})
            
            # Generate streaming response
            text_stream = self.generate_streaming_response(messages, detected_mode)
            
            # Stream to ElevenLabs and get full response
            full_response = await self.stream_to_elevenlabs(text_stream, call_sid)
            
            return full_response
            
        except Exception as e:
            logger.error(f"Default mode processing error: {e}")
            return "I'm here to help. What can I do for you?"
    
    async def handle_interruption(self, call_sid: str):
        """Handle user interruption during AI response"""
        try:
            self.user_speaking = True
            
            if self.realtime_ws:
                # Cancel current response in realtime mode
                cancel_message = {
                    "type": "response.cancel"
                }
                await self.realtime_ws.send(json.dumps(cancel_message))
            
            # Stop ElevenLabs streaming
            # TODO: Implement ElevenLabs stream cancellation
            
            logger.info(f"Handled interruption for {call_sid}")
            
        except Exception as e:
            logger.error(f"Interruption handling error: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status for dashboard"""
        return {
            "current_mode": self.current_mode,
            "openai_connected": bool(self.openai_client),
            "realtime_active": bool(self.realtime_ws and not self.realtime_ws.closed),
            "processing": self.is_processing,
            "models": self.models
        }

# Global instance
openai_assistant = OpenAIRealtimeAssistant()