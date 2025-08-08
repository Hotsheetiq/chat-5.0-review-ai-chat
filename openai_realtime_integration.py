"""
OpenAI Real-time Voice Assistant Integration
Supports streaming responses, voice activity detection, and model switching
"""

import os
import json
import logging
import asyncio
import websockets
import time
from typing import Optional, AsyncGenerator
from openai import OpenAI
import threading
from queue import Queue
import base64

logger = logging.getLogger(__name__)

class OpenAIRealtimeAssistant:
    """Real-time voice assistant using OpenAI streaming APIs"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.current_model = "gpt-4o-mini"  # Default fast model
        self.conversation_context = []
        self.stream_active = False
        self.response_queue = Queue()
        
        # Property management system context
        self.system_prompt = """You are Chris, an AI assistant for Grinberg Management property management company. You're naturally helpful, friendly, and professional.

Key Information:
- Office: 31 Port Richmond Avenue, Staten Island, NY
- Hours: Monday-Friday, 9 AM - 5 PM Eastern Time
- Phone transfers: (718) 414-6984 for Diane or Janier
- Manage properties: 25, 29, 31 Port Richmond Ave; 122 Targee St; 2940 Richmond Ave

Capabilities:
- Handle maintenance requests with empathy and urgency
- Verify tenant addresses and create service issues
- Provide property information and office hours
- Transfer complex issues to human staff

Response Style:
- Keep responses under 40 words for real-time conversation
- Sound natural and conversational, not robotic
- Show genuine care for tenant problems
- Be upbeat but professional"""

    def should_use_reasoning_model(self, user_input: str) -> bool:
        """Detect if we need heavy reasoning (switch to GPT-4.1/5.0)"""
        reasoning_keywords = [
            'complex', 'analyze', 'calculate', 'legal', 'complicated',
            'multiple', 'several', 'various', 'explain in detail',
            'breakdown', 'comprehensive', 'thorough analysis'
        ]
        
        return any(keyword in user_input.lower() for keyword in reasoning_keywords)

    async def stream_openai_response(self, messages: list, max_tokens: int = 100) -> AsyncGenerator[str, None]:
        """Stream response tokens from OpenAI as they arrive"""
        try:
            # Switch model if needed for complex reasoning
            current_input = messages[-1].get('content', '') if messages else ''
            model = "gpt-4o" if self.should_use_reasoning_model(current_input) else self.current_model
            
            logger.info(f"Using model: {model} for streaming response")
            
            # Create streaming completion
            stream = self.openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
                stream=True  # Enable streaming
            )
            
            # Stream tokens as they arrive
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    token = chunk.choices[0].delta.content
                    yield token
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield "I'm having trouble processing that right now. How else can I help?"

    async def process_voice_input(self, audio_data: bytes, call_sid: str) -> AsyncGenerator[str, None]:
        """Process voice input and stream back text tokens for TTS"""
        try:
            # Convert audio to text using Whisper
            transcript = await self.transcribe_audio(audio_data)
            
            if not transcript:
                yield "I didn't catch that. Could you repeat?"
                return
                
            logger.info(f"Transcribed: {transcript}")
            
            # Build conversation context
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add recent conversation history (last 6 messages)
            messages.extend(self.conversation_context[-6:])
            
            # Add current user input
            messages.append({"role": "user", "content": transcript})
            
            # Stream AI response tokens
            full_response = ""
            async for token in self.stream_openai_response(messages):
                full_response += token
                yield token
                
            # Save to conversation history
            self.conversation_context.append({"role": "user", "content": transcript})
            self.conversation_context.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            logger.error(f"Voice processing error: {e}")
            yield "I encountered an issue. What can I help you with?"

    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper"""
        try:
            # Create temporary audio file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                # Transcribe using Whisper
                with open(temp_file.name, 'rb') as audio_file:
                    transcript = self.openai_client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="en"
                    )
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                return transcript.text.strip() if transcript.text else ""
                
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    def handle_interruption(self):
        """Handle user interruption (barge-in capability)"""
        logger.info("User interruption detected - stopping AI response")
        self.stream_active = False
        
        # Clear response queue
        while not self.response_queue.empty():
            try:
                self.response_queue.get_nowait()
            except:
                break

    def reset_conversation(self, call_sid: str):
        """Reset conversation context for new call"""
        self.conversation_context = []
        self.stream_active = False
        logger.info(f"Reset conversation context for call {call_sid}")

    async def generate_simple_response(self, user_input: str) -> str:
        """Generate simple non-streaming response for basic queries"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=self.current_model,
                messages=messages,
                max_tokens=80,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Simple response error: {e}")
            return "I'm here to help. What can I do for you?"

    def get_voice_activity_detection_settings(self) -> dict:
        """Return VAD settings for real-time conversation"""
        return {
            "silence_threshold": 0.5,  # Seconds of silence before considering speech ended
            "speech_timeout": 8.0,     # Max seconds for user speech
            "interruption_threshold": 0.3  # Seconds to detect interruption
        }

# Global instance for the assistant
realtime_assistant = OpenAIRealtimeAssistant()

async def handle_realtime_conversation(websocket, call_sid: str):
    """Handle real-time conversation via WebSocket"""
    logger.info(f"Starting real-time conversation for call {call_sid}")
    
    try:
        # Reset conversation for new call
        realtime_assistant.reset_conversation(call_sid)
        
        async for message in websocket:
            try:
                data = json.loads(message)
                
                if data.get('event') == 'media':
                    # Process incoming audio
                    audio_payload = data.get('media', {}).get('payload')
                    if audio_payload:
                        # Decode base64 audio
                        audio_data = base64.b64decode(audio_payload)
                        
                        # Process and stream response
                        async for token in realtime_assistant.process_voice_input(audio_data, call_sid):
                            # Send token to ElevenLabs for immediate TTS
                            await websocket.send(json.dumps({
                                'event': 'response_token',
                                'token': token,
                                'call_sid': call_sid
                            }))
                
                elif data.get('event') == 'stop':
                    # User interrupted - handle barge-in
                    realtime_assistant.handle_interruption()
                    
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message}")
            except Exception as e:
                logger.error(f"Message handling error: {e}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket connection closed for call {call_sid}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        # Cleanup
        realtime_assistant.reset_conversation(call_sid)

    def create_realtime_response(self, user_input: str, call_sid: str = None) -> str:
        """Create a quick response for immediate use (non-streaming fallback)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(
                self.generate_simple_response(user_input)
            )
            loop.close()
            return response
        except Exception as e:
            logger.error(f"Realtime response error: {e}")
            return "I'm here to help. How can I assist you today?"

def create_realtime_response(user_input: str, call_sid: str = None) -> str:
    """Global function for creating realtime responses"""
    return realtime_assistant.create_realtime_response(user_input, call_sid)