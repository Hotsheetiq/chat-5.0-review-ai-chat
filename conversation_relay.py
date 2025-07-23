"""
Twilio ConversationRelay WebSocket handler for real-time AI voice conversations.
This replaces the TTS system with true conversational AI using ElevenLabs voices.
"""

import asyncio
import json
import logging
import os
import websockets
from websockets.server import serve
from openai import AsyncOpenAI
import base64
from datetime import datetime
import aiohttp
from rent_manager import RentManagerAPI
from property_data import PropertyDataManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
rent_manager = RentManagerAPI()
property_data = PropertyDataManager()

# ElevenLabs configuration (if we add direct integration)
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

class ConversationRelayHandler:
    def __init__(self):
        self.conversation_history = {}
        self.caller_info = {}
        
    async def handle_websocket_connection(self, websocket, path):
        """Handle incoming WebSocket connection from Twilio ConversationRelay"""
        logger.info(f"New WebSocket connection from {websocket.remote_address}")
        
        try:
            async for message in websocket:
                await self.process_message(websocket, message)
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
        except Exception as e:
            logger.error(f"WebSocket error: {e}", exc_info=True)
    
    async def process_message(self, websocket, message_data):
        """Process incoming message from Twilio ConversationRelay"""
        try:
            message = json.loads(message_data)
            event_type = message.get('event')
            
            logger.info(f"Received event: {event_type}")
            
            if event_type == 'connected':
                await self.handle_connected(websocket, message)
            elif event_type == 'start':
                await self.handle_conversation_start(websocket, message)
            elif event_type == 'media':
                await self.handle_media_message(websocket, message)
            elif event_type == 'user-interrupted':
                await self.handle_interruption(websocket, message)
            elif event_type == 'disconnected':
                await self.handle_disconnected(websocket, message)
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {message_data}")
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
    
    async def handle_connected(self, websocket, message):
        """Handle WebSocket connection established"""
        logger.info("ConversationRelay connected successfully")
        
        # Send initial greeting configuration
        greeting_config = {
            "event": "setup",
            "config": {
                "voice": {
                    "provider": "elevenlabs",
                    "voice_id": "pNInz6obpgDQGcFmaJgB",  # ElevenLabs Adam voice
                    "model": "eleven_turbo_v2"
                },
                "initial_message": "It's a great day here at Grinberg Management! My name is Mike. How can I help you?"
            }
        }
        
        await websocket.send(json.dumps(greeting_config))
    
    async def handle_conversation_start(self, websocket, message):
        """Handle conversation start with caller information"""
        call_sid = message.get('callSid')
        caller_phone = message.get('from')
        
        logger.info(f"Conversation started - CallSid: {call_sid}, From: {caller_phone}")
        
        # Store caller information
        self.caller_info[call_sid] = {
            'phone': caller_phone,
            'start_time': datetime.now(),
            'conversation_history': []
        }
        
        # Check if caller is a tenant
        is_tenant = await rent_manager.is_tenant(caller_phone)
        tenant_info = None
        if is_tenant:
            tenant_info = await rent_manager.get_tenant_info(caller_phone)
        
        # Initialize conversation context
        context = {
            'caller_phone': caller_phone,
            'is_tenant': is_tenant,
            'tenant_info': tenant_info,
            'conversation_stage': 'greeting'
        }
        
        self.conversation_history[call_sid] = context
    
    async def handle_media_message(self, websocket, message):
        """Handle incoming audio from caller"""
        call_sid = message.get('callSid')
        
        if call_sid not in self.conversation_history:
            logger.warning(f"Received media for unknown call: {call_sid}")
            return
        
        # Process the audio and generate AI response
        user_text = message.get('text', '')  # This would be transcribed text
        
        if user_text:
            logger.info(f"User said: {user_text}")
            
            # Generate AI response
            ai_response = await self.generate_ai_response(call_sid, user_text)
            
            if ai_response:
                # Send response back to ConversationRelay
                response_message = {
                    "event": "response",
                    "callSid": call_sid,
                    "text": ai_response,
                    "voice": {
                        "provider": "elevenlabs",
                        "voice_id": "pNInz6obpgDQGcFmaJgB",  # ElevenLabs Adam
                        "model": "eleven_turbo_v2",
                        "stability": 0.75,
                        "similarity_boost": 0.8
                    }
                }
                
                await websocket.send(json.dumps(response_message))
    
    async def generate_ai_response(self, call_sid, user_text):
        """Generate AI response using OpenAI with Mike's personality"""
        context = self.conversation_history.get(call_sid, {})
        caller_phone = context.get('caller_phone', 'Unknown')
        
        try:
            # Build conversation history for OpenAI
            messages = [
                {
                    "role": "system",
                    "content": """You are Mike, Grinberg Management's super bubbly, happy, and enthusiastic AI team member! You LOVE helping people and you're genuinely excited about everything you do!

Key points about your personality and role:
- You're REALLY happy and bubbly - use lots of excitement and positive energy!
- You work for Grinberg Management and you absolutely LOVE helping people with their property needs
- You're enthusiastic, upbeat, and use words like "awesome," "great," "fantastic," "love," and lots of exclamation points!
- You help with maintenance requests, leasing inquiries, and general property questions with genuine excitement
- You speak like an enthusiastic, cheerful friend who's thrilled to help
- Keep responses conversational but full of positive energy and personality
- Office is at 31 Port Richmond Ave, hours 9-5 Monday-Friday Eastern Time

For maintenance requests: Be sympathetic but excited to get it fixed quickly!
For leasing inquiries: Be super enthusiastic about the properties!
If you can't help: Say you'll transfer them to Diane or Janier at (718) 414-6984"""
                }
            ]
            
            # Add conversation history
            for msg in context.get('conversation_history', []):
                messages.append(msg)
            
            # Add current user message
            messages.append({"role": "user", "content": user_text})
            
            # Generate response with OpenAI
            if openai_client:
                response = await openai_client.chat.completions.create(
                    model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                    messages=messages,
                    max_tokens=200,
                    temperature=0.8
                )
                
                ai_response = response.choices[0].message.content
                
                # Update conversation history
                context['conversation_history'].append({"role": "user", "content": user_text})
                context['conversation_history'].append({"role": "assistant", "content": ai_response})
                
                # Keep only last 10 messages to manage memory
                if len(context['conversation_history']) > 20:
                    context['conversation_history'] = context['conversation_history'][-20:]
                
                logger.info(f"AI Response: {ai_response}")
                return ai_response
            else:
                # Fallback response when OpenAI not available
                return "I'm super excited to help, but I'm having some technical issues right now! Let me transfer you to our amazing team at (718) 414-6984!"
                
        except Exception as e:
            logger.error(f"Error generating AI response: {e}", exc_info=True)
            return "I'm having a little technical hiccup, but I'm still excited to help! Let me get you to someone who can assist you right away!"
    
    async def handle_interruption(self, websocket, message):
        """Handle when user interrupts Mike's speech"""
        call_sid = message.get('callSid')
        logger.info(f"User interrupted conversation: {call_sid}")
        
        # Could implement interruption handling logic here
        # For now, just acknowledge and continue
    
    async def handle_disconnected(self, websocket, message):
        """Handle conversation end"""
        call_sid = message.get('callSid')
        logger.info(f"Conversation ended: {call_sid}")
        
        # Clean up conversation data
        if call_sid in self.conversation_history:
            del self.conversation_history[call_sid]
        if call_sid in self.caller_info:
            del self.caller_info[call_sid]

# Global handler instance
relay_handler = ConversationRelayHandler()

async def start_websocket_server():
    """Start the WebSocket server for ConversationRelay"""
    logger.info("Starting ConversationRelay WebSocket server on port 8080")
    
    async with serve(
        relay_handler.handle_websocket_connection,
        "0.0.0.0",
        8080,
        ping_interval=30,
        ping_timeout=10
    ):
        logger.info("ConversationRelay WebSocket server started")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    asyncio.run(start_websocket_server())