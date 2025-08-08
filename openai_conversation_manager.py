"""
OpenAI Conversation Manager - Implements Three-Mode System with Memory
Handles Default, Live, and Reasoning modes with conversation context
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
import time

logger = logging.getLogger(__name__)

class OpenAIConversationManager:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.conversation_histories = {}  # Call-specific histories
        self.current_mode = "default"  # default, live, reasoning
        
        # System prompt for Chris
        self.system_prompt = {
            "role": "system",
            "content": "You are Chris, a helpful property management voice assistant. Answer questions directly without repeating greetings unless it's the first interaction."
        }
    
    def get_conversation_history(self, call_sid: str) -> List[ChatCompletionMessageParam]:
        """Get conversation history for a specific call, maintaining only last 10 turns"""
        if call_sid not in self.conversation_histories:
            self.conversation_histories[call_sid] = [self.system_prompt]
        
        history = self.conversation_histories[call_sid]
        
        # Keep system prompt + last 10 user/assistant pairs (20 messages max)
        if len(history) > 21:  # System + 20 messages
            # Keep system prompt and last 20 messages
            self.conversation_histories[call_sid] = [history[0]] + history[-20:]
            
        return self.conversation_histories[call_sid]
    
    def add_to_history(self, call_sid: str, role: str, content: str):
        """Add message to conversation history"""
        if not content or len(content.strip()) < 3:
            logger.warning(f"Skipping empty/short message: '{content}'")
            return
            
        history = self.get_conversation_history(call_sid)
        history.append({"role": role, "content": content.strip()})  # type: ignore
        
        # Trim to maintain size limits
        if len(history) > 21:
            self.conversation_histories[call_sid] = [history[0]] + history[-20:]
    
    def should_use_reasoning_mode(self, text: str) -> bool:
        """Detect if query requires reasoning mode (complex, multi-step, high-stakes)"""
        reasoning_triggers = [
            "analyze", "compare", "pros and cons", "evaluate", "assessment",
            "legal", "zoning", "convert", "investment", "financial analysis",
            "regulation", "compliance", "market analysis", "feasibility",
            "long-term", "strategy", "recommend", "detailed analysis"
        ]
        
        text_lower = text.lower()
        
        # Check for complex triggers
        trigger_count = sum(1 for trigger in reasoning_triggers if trigger in text_lower)
        
        # Use reasoning if multiple triggers or long complex query
        return trigger_count >= 2 or (len(text) > 100 and trigger_count >= 1)
    
    async def process_default_mode(self, call_sid: str, user_text: str) -> Tuple[str, float]:
        """Default mode: STT → gpt-4o-mini → stream tokens to ElevenLabs"""
        start_time = time.time()
        
        try:
            # Validate input
            if len(user_text.strip()) < 3:
                return "I didn't quite catch that. Could you please repeat what you need help with?", 0.1
            
            # Add user message to history
            self.add_to_history(call_sid, "user", user_text)
            
            # Get conversation history
            messages = self.get_conversation_history(call_sid)
            
            logger.info(f"Processing with {len(messages)} messages in history")
            
            # Call OpenAI with streaming
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
                max_tokens=150,
                temperature=0.7
            )
            
            # Collect streamed response
            response_text = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
            
            # Add assistant response to history
            self.add_to_history(call_sid, "assistant", response_text)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Default mode response ({processing_time:.3f}s): {response_text[:100]}...")
            
            return response_text.strip(), processing_time
            
        except Exception as e:
            logger.error(f"Default mode error: {e}")
            return "I'm experiencing a technical issue. Please try again in a moment.", 0.1
    
    async def process_live_mode(self, call_sid: str, user_text: str) -> Tuple[str, float]:
        """Live mode: gpt-4o-mini-realtime with VAD (simulated for now)"""
        start_time = time.time()
        
        try:
            # Validate input
            if len(user_text.strip()) < 3:
                return "Could you please clarify what you need?", 0.05
            
            # Add user message to history
            self.add_to_history(call_sid, "user", user_text)
            
            # Get conversation history
            messages = self.get_conversation_history(call_sid)
            
            # Simulate realtime API with faster response
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
                max_tokens=100,
                temperature=0.8
            )
            
            # Simulate streaming to TTS immediately
            response_text = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
                    # In real implementation, stream each token to ElevenLabs immediately
            
            # Add assistant response to history
            self.add_to_history(call_sid, "assistant", response_text)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Live mode response ({processing_time:.3f}s): {response_text[:100]}...")
            
            return response_text.strip(), processing_time
            
        except Exception as e:
            logger.error(f"Live mode error: {e}")
            return "I'm having trouble processing that. What else can I help with?", 0.05
    
    async def process_reasoning_mode(self, call_sid: str, user_text: str) -> Tuple[str, float]:
        """Reasoning mode: gpt-4o for complex analysis"""
        start_time = time.time()
        
        try:
            # Validate input
            if len(user_text.strip()) < 3:
                return "I need more details to provide a thorough analysis. Could you elaborate?", 0.1
            
            # Add user message to history
            self.add_to_history(call_sid, "user", user_text)
            
            # Get conversation history
            messages = self.get_conversation_history(call_sid)
            
            # Enhanced system prompt for reasoning
            reasoning_messages = [
                {
                    "role": "system", 
                    "content": "You are Chris, an expert property management consultant with deep knowledge of real estate law, zoning, and financial analysis. Provide thorough, analytical responses with specific reasoning."
                }
            ] + messages[1:]  # Skip original system prompt
            
            logger.info(f"Using reasoning mode for complex query: {user_text[:50]}...")
            
            # Use gpt-4o for reasoning
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=reasoning_messages,
                stream=True,
                max_tokens=300,
                temperature=0.6
            )
            
            # Collect response
            response_text = ""
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
            
            # Add assistant response to history
            self.add_to_history(call_sid, "assistant", response_text)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Reasoning mode response ({processing_time:.3f}s): {response_text[:100]}...")
            
            return response_text.strip(), processing_time
            
        except Exception as e:
            logger.error(f"Reasoning mode error: {e}")
            return "I need a moment to analyze this properly. Could you ask me something else while I process that?", 0.1
    
    async def process_user_input(self, call_sid: str, user_text: str, force_mode: Optional[str] = None) -> Tuple[str, str, float]:
        """Main processing function that routes to appropriate mode"""
        
        # Determine mode
        if force_mode:
            mode = force_mode
        elif self.should_use_reasoning_mode(user_text):
            mode = "reasoning"
            logger.info(f"Auto-selected reasoning mode for: {user_text[:50]}...")
        elif self.current_mode == "live":
            mode = "live"
        else:
            mode = "default"
        
        # Process based on mode
        if mode == "reasoning":
            response_text, processing_time = await self.process_reasoning_mode(call_sid, user_text)
        elif mode == "live":
            response_text, processing_time = await self.process_live_mode(call_sid, user_text)
        else:
            response_text, processing_time = await self.process_default_mode(call_sid, user_text)
        
        return response_text, mode, processing_time
    
    def set_mode(self, mode: str):
        """Set the current conversation mode"""
        if mode in ["default", "live", "reasoning"]:
            self.current_mode = mode
            logger.info(f"Switched to {mode} mode")
        else:
            logger.warning(f"Invalid mode: {mode}")
    
    def clear_history(self, call_sid: str):
        """Clear conversation history for a call"""
        self.conversation_histories[call_sid] = [self.system_prompt]
        logger.info(f"Cleared history for call {call_sid}")
    
    def get_history_summary(self, call_sid: str) -> Dict:
        """Get summary of conversation history"""
        history = self.get_conversation_history(call_sid)
        
        user_messages = [msg for msg in history if msg["role"] == "user"]
        assistant_messages = [msg for msg in history if msg["role"] == "assistant"]
        
        return {
            "total_messages": len(history) - 1,  # Exclude system prompt
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "current_mode": self.current_mode,
            "last_user_message": user_messages[-1]["content"] if user_messages else None,
            "last_assistant_message": assistant_messages[-1]["content"] if assistant_messages else None
        }

# Global instance
conversation_manager = OpenAIConversationManager()