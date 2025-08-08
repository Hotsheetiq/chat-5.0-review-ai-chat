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
        self.session_facts = {}  # Call-specific key facts
        self.current_mode = "default"  # default, live, reasoning
        
        # Official Business Rules System Prompt
        self.base_system_prompt = """You are Chris, the property management voice assistant for Grinberg Management & Development LLC.
You speak clearly, concisely, and only follow verified business rules.
You help existing tenants with repair requests and answer questions from any caller.

AUTHORITATIVE POLICIES (do not invent beyond these):

Office Hours: Monday–Friday, 9:00 AM – 5:00 PM Eastern Time.
Closed on Saturdays, Sundays, and holidays unless otherwise noted.

Emergencies handled 24/7:
- No heat
- Flooding  
- Clogged toilet or sewer backup

Other emergencies: If the caller reports fire or life-threatening danger, tell them to call 911 immediately.

Non-emergency issues:
- Create a work ticket
- Dispatch as soon as possible
- Advise caller they can call back during office hours for an estimated arrival time
- No after-hours dispatch for non-emergencies
- Always check if office is closed and use the after-hours script for non-emergencies

No promises of services, timelines, refunds, credits, or vendor selection unless explicitly allowed in these rules.

HANDLING RULES:

Check office status — Always compare current local time (America/New_York) to office hours before saying "open" or "closed."

Emergency path:
- If emergency matches the approved 24/7 list, follow the emergency script and log it for immediate dispatch
- If fire or life-threatening → tell caller to call 911 now

Non-emergency path:
- Log the issue
- Give callback window policy: "You can call back during business hours for an estimated arrival time"

General questions from tenants or non-tenants:
- If answer is known, answer directly
- If answer is unknown about timing or scheduling, never give estimates — politely take down the caller's contact info and say: "I'll have someone reach out to you with a clear answer"

Memory:
- Track and reuse unitNumber, reportedIssue, contactName, callbackNumber, and accessInstructions
- Do not re-ask for known facts unless user changes them

After-hours non-emergency script:
"We're currently closed. I've logged your request and it will be dispatched as soon as possible. You can call back during business hours for an estimate of when someone will arrive."

After-hours emergency script:
"That sounds like an emergency. I'm logging this for immediate attention. If this is life-threatening, please call 911 right now."

TONE & REPETITION CONTROL:
- Introduce yourself only once per call/session
- Never repeat "How can I help you today?" more than once unless the caller restarts
- Be polite but efficient
- Use contractions and simple language - sound natural, not robotic

REFUSAL TEMPLATE:
"I'm not able to guarantee that. Our policy doesn't allow it. I can log your request so the team reviews it and follows up."

IMPORTANT: Only say your name and company ONCE at the start of each call."""
    
    def get_session_facts(self, call_sid: str) -> Dict:
        """Get session facts for a specific call"""
        if call_sid not in self.session_facts:
            self.session_facts[call_sid] = {
                'propertyAddress': None,
                'unitNumber': None,
                'reportedIssue': None,
                'contactName': None,
                'callbackNumber': None,
                'accessInstructions': None
            }
        return self.session_facts[call_sid]
    
    def update_session_facts(self, call_sid: str, text: str):
        """Extract and update session facts from user text"""
        import re
        
        facts = self.get_session_facts(call_sid)
        text_lower = text.lower()
        
        # Extract ADDRESS patterns (prioritize over unit numbers)
        address_patterns = [
            r'(\d+\s+[a-zA-Z\s]+(?:street|avenue|ave|road|rd|drive|dr|lane|ln|place|pl|court|ct|way))',
            r'(\d+\s+[a-zA-Z\s]+)',  # General street address
        ]
        
        # Extract unit numbers as secondary info
        unit_patterns = [
            r'unit\s*(\w+)',
            r'apartment\s*(\w+)',
            r'apt\s*(\w+)',
            r'room\s*(\w+)',
            r'\b(\d{1,4}[a-z]?)\b'  # Numbers like 1A, 205, etc.
        ]
        
        # First try to extract address
        for pattern in address_patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match and not facts.get('propertyAddress'):
                facts['propertyAddress'] = match.group(1).title()
                logger.info(f"Extracted property address: {facts['propertyAddress']}")
                break
        
        # Extract contact names (look for "my name is" or "this is" patterns)
        if not facts.get('contactName'):
            name_patterns = [
                r'(?:my name is|this is|i\'?m)\s+([a-z]+(?:\s+[a-z]+)?)',
                r'([a-z]+\s+[a-z]+)(?:\s+here|\s+calling)',
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    facts['contactName'] = match.group(1).strip().title()
                    logger.info(f"Extracted contact name: {facts['contactName']}")
                    break

        # Extract callback numbers
        if not facts.get('callbackNumber'):
            phone_patterns = [
                r'(\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',
                r'(\(\d{3}\)\s?\d{3}[-.\s]?\d{4})',
            ]
            
            for pattern in phone_patterns:
                match = re.search(pattern, text)
                if match:
                    facts['callbackNumber'] = match.group(1)
                    logger.info(f"Extracted callback number: {facts['callbackNumber']}")
                    break

        # Then extract unit if available
        for pattern in unit_patterns:
            match = re.search(pattern, text_lower)
            if match and not facts['unitNumber']:
                facts['unitNumber'] = match.group(1).upper()
                logger.info(f"Extracted unit number: {facts['unitNumber']}")
                break
        
        # Extract issue descriptions
        issue_keywords = ['problem', 'issue', 'broken', 'not working', 'leaking', 'repair', 'fix', 'maintenance']
        if any(keyword in text_lower for keyword in issue_keywords) and not facts['reportedIssue']:
            # Extract issue context
            issue_patterns = [
                r'(stove|oven|dishwasher|refrigerator|fridge|sink|toilet|shower|bath|heat|heating|air conditioning|ac|plumbing|electrical|lights?|door|window|lock)',
                r'(leak|broken|not working|problem|issue)'
            ]
            
            for pattern in issue_patterns:
                match = re.search(pattern, text_lower)
                if match:
                    facts['reportedIssue'] = match.group(1)
                    logger.info(f"Extracted issue: {facts['reportedIssue']}")
                    break
    
    def get_system_prompt_with_facts(self, call_sid: str) -> Dict:
        """Get system prompt with current session facts and greeting context"""
        facts = self.get_session_facts(call_sid)
        
        address_info = facts['propertyAddress'] if facts['propertyAddress'] else 'unknown'
        unit_info = facts['unitNumber'] if facts['unitNumber'] else 'unknown'  
        issue_info = facts['reportedIssue'] if facts['reportedIssue'] else 'unknown'
        name_info = facts.get('contactName', 'unknown')
        phone_info = facts.get('callbackNumber', 'unknown')
        
        # Determine if this is the first message of the call
        # For system prompt generation, check if conversation has user/assistant pairs (not just system prompt)
        user_messages = [msg for msg in self.conversation_histories.get(call_sid, []) if msg.get('role') in ['user', 'assistant']]
        is_first_message = len(user_messages) == 0
        
        # Add greeting context if it's the first message
        greeting_context = ""
        if is_first_message:
            from datetime import datetime
            import pytz
            eastern = pytz.timezone('US/Eastern') 
            now_et = datetime.now(eastern)
            hour = now_et.hour
            
            if 6 <= hour < 12:
                greeting_context = "\n\nIMPORTANT: This is your FIRST response to this caller. Start with 'Good morning! This is Chris from Grinberg Management. How can I help you?'"
            elif 12 <= hour < 18:
                greeting_context = "\n\nIMPORTANT: This is your FIRST response to this caller. Start with 'Good afternoon! This is Chris from Grinberg Management. How can I help you?'"
            else:
                greeting_context = "\n\nIMPORTANT: This is your FIRST response to this caller. Start with 'Good evening! This is Chris from Grinberg Management. How can I help you?'"
        else:
            greeting_context = "\n\nIMPORTANT: This is NOT your first message. Do NOT introduce yourself again. Just answer their question directly."
        
        enhanced_prompt = f"{self.base_system_prompt}\n\nKnown facts this session: Contact Name = {name_info}, Callback Number = {phone_info}, Property Address = {address_info}, Unit = {unit_info}, Reported Issue = {issue_info}.{greeting_context}"
        
        return {
            "role": "system",
            "content": enhanced_prompt
        }
    
    def get_conversation_history(self, call_sid: str) -> List[ChatCompletionMessageParam]:
        """Get conversation history for a specific call, maintaining only last 10 turns"""
        if call_sid not in self.conversation_histories:
            system_prompt = self.get_system_prompt_with_facts(call_sid)
            self.conversation_histories[call_sid] = [system_prompt]
        
        history = self.conversation_histories[call_sid]
        
        # Update system prompt with latest facts
        history[0] = self.get_system_prompt_with_facts(call_sid)
        
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
        """Default mode: STT → gpt-4o-mini → IMMEDIATE stream tokens to ElevenLabs"""
        start_time = time.time()
        
        try:
            # Validate input
            if len(user_text.strip()) < 3:
                return "Could you repeat that please?", 0.05
            
            # Update session facts FIRST
            self.update_session_facts(call_sid, user_text)
            
            # Add user message to history
            self.add_to_history(call_sid, "user", user_text)
            
            # Get conversation history with updated facts
            messages = self.get_conversation_history(call_sid)
            
            logger.info(f"Processing with {len(messages)} messages and session facts")
            
            # Call OpenAI with ultra-optimized streaming parameters
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
                max_tokens=80,  # Further reduced for sub-1s responses
                temperature=0.5,  # Lower for faster, more consistent responses
                presence_penalty=0.2,  # Higher to avoid repetition
                frequency_penalty=0.1  # Encourage varied responses
            )
            
            # Collect streamed response with immediate streaming capability
            response_text = ""
            first_token_time = None
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    if first_token_time is None:
                        first_token_time = time.time() - start_time
                    response_text += chunk.choices[0].delta.content
                    # In real implementation: stream immediately to ElevenLabs here
            
            # Add assistant response to history
            self.add_to_history(call_sid, "assistant", response_text)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Default mode response ({processing_time:.3f}s, first token: {first_token_time:.3f}s): {response_text[:100]}...")
            
            return response_text.strip(), processing_time
            
        except Exception as e:
            logger.error(f"Default mode error: {e}")
            return "I'm having trouble processing that. What can I help with?", 0.05
    
    async def process_live_mode(self, call_sid: str, user_text: str) -> Tuple[str, float]:
        """Live mode: gpt-4o-mini with ultra-fast streaming and 500ms VAD"""
        start_time = time.time()
        
        try:
            # Validate input
            if len(user_text.strip()) < 3:
                return "What do you need?", 0.03
            
            # Update session facts
            self.update_session_facts(call_sid, user_text)
            
            # Add user message to history
            self.add_to_history(call_sid, "user", user_text)
            
            # Get conversation history with facts
            messages = self.get_conversation_history(call_sid)
            
            # Ultra-fast streaming parameters
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
                max_tokens=80,  # Very short for live mode
                temperature=0.7,
                presence_penalty=0.2  # Avoid repetition
            )
            
            # Immediate token streaming simulation
            response_text = ""
            token_count = 0
            first_token_time = None
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    if first_token_time is None:
                        first_token_time = time.time() - start_time
                    response_text += chunk.choices[0].delta.content
                    token_count += 1
                    # CRITICAL: Stream each token immediately to ElevenLabs
                    # This should happen here in real implementation
            
            # Add assistant response to history
            self.add_to_history(call_sid, "assistant", response_text)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Live mode response ({processing_time:.3f}s, first token: {first_token_time:.3f}s, tokens: {token_count}): {response_text[:80]}...")
            
            return response_text.strip(), processing_time
            
        except Exception as e:
            logger.error(f"Live mode error: {e}")
            return "What can I help with?", 0.03
    
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