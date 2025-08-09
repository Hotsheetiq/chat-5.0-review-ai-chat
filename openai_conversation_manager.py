"""
OpenAI Conversation Manager - Implements Three-Mode System with Memory
Handles Default, Live, and Reasoning modes with conversation context
ABSOLUTE NO GROK POLICY - OpenAI-only implementation
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
import re

logger = logging.getLogger(__name__)

class OpenAIConversationManager:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.conversation_histories = {}  # Call-specific histories
        self.session_facts = {}  # Call-specific key facts
        self.current_mode = "default"  # default, live, reasoning
        self.streaming_sessions = {}  # Active streaming sessions
        
        # Grok usage guard - ABSOLUTE NO GROK POLICY
        self.grok_guard_active = True
        
        # Official Business Rules System Prompt
        self.base_system_prompt = """You are Chris, the property management voice assistant for Grinberg Management & Development LLC.
You speak clearly, concisely, and only follow verified business rules.
You help existing tenants with repair requests and answer questions from any caller.

AUTHORITATIVE POLICIES (do not invent beyond these):

Office Hours: Monday-Friday, 9:00 AM - 5:00 PM Eastern Time.
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

Check office status - Always compare current local time (America/New_York) to office hours before saying "open" or "closed."

Emergency path:
- If emergency matches the approved 24/7 list, follow the emergency script and log it for immediate dispatch
- If fire or life-threatening -> tell caller to call 911 now

Non-emergency path:
- Log the issue
- Give callback window policy: "You can call back during business hours for an estimated arrival time"

General questions from tenants or non-tenants:
- If answer is known, answer directly
- If answer is unknown about timing or scheduling, never give estimates - politely take down the caller's contact info and say: "I'll have someone reach out to you with a clear answer"

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
        
    def detect_grok_usage(self, context):
        """Runtime guard to prevent any Grok usage"""
        if any(term in str(context).lower() for term in ['grok', 'xai', 'x.ai']):
            logger.error("🚨 GROK USAGE DETECTED - STOPPING")
            raise Exception("Grok usage detected — migrate to OpenAI.")
    
    def test_streaming(self):
        """Test OpenAI streaming capability for mode selection"""
        try:
            # Quick test of streaming API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": "test"}],
                stream=True,
                max_tokens=5
            )
            # Try to get first chunk
            next(response)
            return True
        except Exception as e:
            logger.error(f"OpenAI streaming test failed: {e}")
            return False
    
    async def start_streaming_session(self, call_sid):
        """Initialize streaming session for full streaming mode"""
        self.streaming_sessions[call_sid] = {
            'start_time': time.time(),
            'active': True,
            'tokens_streamed': 0
        }
        logger.info(f"🚀 OpenAI streaming session started for {call_sid}")
    
    async def stream_response(self, call_sid, context):
        """Stream OpenAI response token by token for full streaming mode"""
        try:
            self.detect_grok_usage(context)
            
            # Build messages with facts injection
            user_input = context.get('user_input', '')
            facts_context = context.get('facts_context', '')
            conversation_history = context.get('conversation_history', [])
            
            # Create enhanced system prompt with facts
            enhanced_system_prompt = f"{self.base_system_prompt}\n\n{facts_context}"
            
            messages = [
                {"role": "system", "content": enhanced_system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Add conversation history
            for msg in conversation_history[-6:]:  # Last 6 messages for context
                messages.append({
                    "role": "assistant" if msg.get('speaker') == 'Chris' else "user",
                    "content": msg.get('message', '')
                })
            
            # Create streaming response
            stream = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                stream=True,
                max_tokens=150,
                temperature=0.7
            )
            
            # Stream tokens
            session = self.streaming_sessions.get(call_sid, {})
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    session['tokens_streamed'] = session.get('tokens_streamed', 0) + 1
                    yield token
                    
        except Exception as e:
            if "Grok usage detected" in str(e):
                raise
            logger.error(f"Streaming response error: {e}")
            yield "I'm here to help. What can I do for you?"
    
    async def cleanup_session(self, call_sid):
        """Clean up streaming session"""
        if call_sid in self.streaming_sessions:
            session = self.streaming_sessions[call_sid]
            duration = time.time() - session['start_time']
            logger.info(f"📊 OpenAI session {call_sid}: {session.get('tokens_streamed', 0)} tokens, {duration:.1f}s")
            del self.streaming_sessions[call_sid]
    
    def get_session_facts(self, call_sid: str) -> Dict:
        """Get session facts for a specific call"""
        if call_sid not in self.session_facts:
            self.session_facts[call_sid] = {
                'propertyAddress': None,
                'unitNumber': None,
                'reportedIssue': None,
                'contactName': None,
                'callbackNumber': None,
                'accessInstructions': None,
                'priority': 'Standard',
                'propertyId': None,
                'unitId': None,
                'tenantId': None,
                'ticketId': None
            }
        return self.session_facts[call_sid]
    
    def extract_session_facts(self, call_sid: str, text: str) -> Dict:
        """Extract and update session facts from user input"""
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
                    facts['reportedIssue'] = match.group(1).title()
                    logger.info(f"Extracted reported issue: {facts['reportedIssue']}")
                    break
        
        # Classify issue priority
        emergency_keywords = ['no heat', 'flooding', 'clogged toilet', 'sewer backup', 'fire']
        if any(keyword in text_lower for keyword in emergency_keywords):
            facts['priority'] = 'Emergency'
        elif 'urgent' in text_lower:
            facts['priority'] = 'Urgent'
        else:
            facts['priority'] = 'Standard'
            
        return facts
    
    async def process_user_input(self, call_sid: str, user_input: str, session_facts: Optional[Dict] = None) -> Tuple[str, str, float]:
        """
        Process user input with three-mode system (default, live, reasoning)
        Returns: (response_text, mode_used, processing_time)
        """
        
        # Guard against Grok usage
        self.detect_grok_usage(user_input)
        
        logger.info(f"Processing user input: {user_input[:50]}...")
        
        # Extract session facts if not provided
        if session_facts is None:
            session_facts = self.extract_session_facts(call_sid, user_input)
        
        start_time = time.time()
        
        try:
            # Auto-select mode based on complexity and latency requirements
            selected_mode = self.select_processing_mode(user_input, session_facts)
            
            if selected_mode == "live":
                response_text = await self.process_live_mode(call_sid, user_input, session_facts)
            elif selected_mode == "reasoning":
                response_text = await self.process_reasoning_mode(call_sid, user_input, session_facts)
            else:
                response_text = await self.process_default_mode(call_sid, user_input, session_facts)
            
            processing_time = time.time() - start_time
            
            # Store conversation history
            self.store_conversation_turn(call_sid, user_input, response_text)
            
            return response_text, selected_mode, processing_time
            
        except Exception as e:
            if "Grok usage detected" in str(e):
                raise
            logger.error(f"Processing error: {e}")
            return "How can I help you today?", "fallback", time.time() - start_time
    
    def select_processing_mode(self, user_input: str, session_facts: Dict) -> str:
        """Auto-select processing mode based on input complexity"""
        # Emergency -> live mode for fastest response
        if session_facts.get('priority') == 'Emergency':
            return "live"
        
        # Complex reasoning needed -> reasoning mode
        complex_keywords = ['policy', 'refund', 'credit', 'legal', 'lease', 'contract', 'explanation']
        if any(keyword in user_input.lower() for keyword in complex_keywords):
            return "reasoning"
        
        # Default mode for standard interactions
        return "default"
    
    async def process_default_mode(self, call_sid: str, user_input: str, session_facts: Dict) -> str:
        """Process using default gpt-4o-mini streaming mode"""
        try:
            messages = self.build_messages_with_facts(user_input, session_facts, call_sid)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=150,
                temperature=0.7,
                stream=False  # Non-streaming for now, can be converted to streaming
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Default mode error: {e}")
            return "I'm here to help. What can I do for you?"
    
    async def process_live_mode(self, call_sid: str, user_input: str, session_facts: Dict) -> str:
        """Process using OpenAI Realtime API for ultra-fast response"""
        try:
            # For now, use fast default mode
            # TODO: Implement actual Realtime API when available
            messages = self.build_messages_with_facts(user_input, session_facts, call_sid)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=80,  # Shorter for speed
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Live mode error: {e}")
            return "I'm here to help. What can I do for you?"
    
    async def process_reasoning_mode(self, call_sid: str, user_input: str, session_facts: Dict) -> str:
        """Process using gpt-4o for heavy reasoning"""
        try:
            messages = self.build_messages_with_facts(user_input, session_facts, call_sid)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Reasoning mode error: {e}")
            return "I'm here to help. What can I do for you?"
    
    def build_messages_with_facts(self, user_input: str, session_facts: Dict, call_sid: str) -> List[Dict]:
        """Build message list with session facts injection"""
        # Build facts context
        known_facts = []
        for key, value in session_facts.items():
            if value and key in ['unitNumber', 'reportedIssue', 'contactName', 'callbackNumber']:
                known_facts.append(f"{key}={value}")
        
        facts_context = f"Known facts: {', '.join(known_facts) if known_facts else 'none yet'}"
        
        # Enhanced system prompt with facts
        enhanced_prompt = f"{self.base_system_prompt}\n\n{facts_context}"
        
        messages = [
            {"role": "system", "content": enhanced_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # Add conversation history
        if call_sid in self.conversation_histories:
            for msg in self.conversation_histories[call_sid][-6:]:  # Last 6 messages
                role = "assistant" if msg.get('speaker') == 'Chris' else "user"
                messages.append({"role": role, "content": msg.get('message', '')})
        
        return messages
    
    def store_conversation_turn(self, call_sid: str, user_input: str, response: str):
        """Store conversation turn in history"""
        if call_sid not in self.conversation_histories:
            self.conversation_histories[call_sid] = []
        
        timestamp = datetime.now().isoformat()
        
        # Store user input
        self.conversation_histories[call_sid].append({
            'timestamp': timestamp,
            'speaker': 'Caller',
            'message': user_input
        })
        
        # Store AI response
        self.conversation_histories[call_sid].append({
            'timestamp': timestamp,
            'speaker': 'Chris',
            'message': response
        })
        
        # Keep only last 20 messages
        if len(self.conversation_histories[call_sid]) > 20:
            self.conversation_histories[call_sid] = self.conversation_histories[call_sid][-20:]

# Global conversation manager instance
conversation_manager = OpenAIConversationManager()