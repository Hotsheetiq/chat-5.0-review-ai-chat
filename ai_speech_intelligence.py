#!/usr/bin/env python3
"""
AI-Powered Speech Intelligence System
Uses Grok AI to understand speech recognition errors through context and reasoning
"""

import logging
import json
from grok_integration import GrokAI

logger = logging.getLogger(__name__)

class AIAddressIntelligence:
    """AI-powered system to understand addresses through intelligent reasoning"""
    
    def __init__(self):
        """Initialize AI speech intelligence system"""
        try:
            self.grok = GrokAI()
            logger.info("✅ AI Speech Intelligence initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AI Speech Intelligence: {e}")
            self.grok = None
    
    def understand_address_intent(self, user_input: str, conversation_context: list = None) -> dict:
        """Use AI to understand what address the caller actually means"""
        if not self.grok:
            return {"understood_address": None, "confidence": 0, "reasoning": "AI not available"}
        
        try:
            # Build intelligent address understanding prompt
            messages = [
                {
                    "role": "system",
                    "content": """You are an intelligent address interpreter for Grinberg Management properties.

MANAGED PROPERTIES:
- 25 Port Richmond Avenue (multi-unit building)
- 29 Port Richmond Avenue (multi-unit building)  
- 31 Port Richmond Avenue (office/commercial)
- 122 Targee Street (multi-unit building)
- 2940 Richmond Avenue (separate property)

SPEECH RECOGNITION INTELLIGENCE:
Use contextual reasoning to understand what callers actually mean when speech recognition creates errors:

COMMON PATTERNS:
- "2540" often means "25" (extra digit added)
- "290" often means "29" (zero added)
- "310" often means "31" (zero added)  
- "1220" often means "122" (zero added)
- "164 richmond" might mean "2940 richmond" (mishearing)
- "port rich" usually means "port richmond"
- "targee" might be heard as "target"

INTELLIGENT REASONING:
- Apply context from conversation to understand intent
- Consider which properties actually exist vs speech errors
- Use probability and context to determine most likely intended address

Respond in JSON format:
{
    "understood_address": "most likely intended address or null",
    "confidence": 0.0-1.0,
    "reasoning": "explanation of your logic",
    "suggestions": ["alternative possibilities"]
}"""
                }
            ]
            
            # Add conversation context if available
            if conversation_context:
                context_summary = " ".join([msg.get('content', '') for msg in conversation_context[-3:]])
                messages.append({
                    "role": "user",
                    "content": f"Conversation context: {context_summary}"
                })
            
            # Add the address to interpret
            messages.append({
                "role": "user", 
                "content": f"Please use AI reasoning to understand this address: '{user_input}'"
            })
            
            # Get AI interpretation
            response = self.grok.generate_response(
                messages=messages,
                max_tokens=200,
                temperature=0.3,  # Lower temperature for more consistent reasoning
                timeout=2.0
            )
            
            # Parse JSON response (handle markdown code blocks)
            try:
                # Remove markdown code block formatting if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]  # Remove '```json'
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]  # Remove '```'
                clean_response = clean_response.strip()
                
                result = json.loads(clean_response)
                logger.info(f"🧠 AI ADDRESS UNDERSTANDING: '{user_input}' → {result.get('understood_address')} (confidence: {result.get('confidence')})")
                logger.info(f"🤔 AI REASONING: {result.get('reasoning')}")
                return result
            except json.JSONDecodeError:
                logger.warning(f"AI returned non-JSON response: {response}")
                return {
                    "understood_address": None,
                    "confidence": 0,
                    "reasoning": "AI response format error",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"AI address understanding failed: {e}")
            return {
                "understood_address": None,
                "confidence": 0,
                "reasoning": f"AI error: {str(e)}"
            }
    
    def understand_maintenance_issue(self, user_input: str, conversation_context: list = None) -> dict:
        """Use AI to understand what maintenance issue the caller is reporting"""
        if not self.grok:
            return {"issue_type": None, "confidence": 0, "reasoning": "AI not available"}
        
        try:
            messages = [
                {
                    "role": "system",
                    "content": """You are an AI maintenance issue classifier for property management.

ISSUE CATEGORIES:
- electrical: power outages, electrical problems, lights not working
- plumbing: toilets, water leaks, bathroom issues, sinks, drains
- heating: no heat, cold apartment, heating system problems
- appliance: washing machine, dishwasher, refrigerator issues
- security: locks, doors, safety concerns
- general: other maintenance needs

Use intelligent reasoning to understand what the caller is reporting, even with unclear speech.

Respond in JSON format:
{
    "issue_type": "category or null",
    "confidence": 0.0-1.0,
    "reasoning": "explanation of classification",
    "urgency": "low/normal/high"
}"""
                }
            ]
            
            # Add conversation context
            if conversation_context:
                context_summary = " ".join([msg.get('content', '') for msg in conversation_context[-3:]])
                messages.append({
                    "role": "user",
                    "content": f"Conversation context: {context_summary}"
                })
            
            messages.append({
                "role": "user",
                "content": f"Classify this maintenance issue: '{user_input}'"
            })
            
            response = self.grok.generate_response(
                messages=messages,
                max_tokens=150,
                temperature=0.3,
                timeout=1.5
            )
            
            try:
                # Remove markdown code block formatting if present
                clean_response = response.strip()
                if clean_response.startswith('```json'):
                    clean_response = clean_response[7:]
                if clean_response.endswith('```'):
                    clean_response = clean_response[:-3]
                clean_response = clean_response.strip()
                
                result = json.loads(clean_response)
                logger.info(f"🔧 AI ISSUE UNDERSTANDING: '{user_input}' → {result.get('issue_type')} (confidence: {result.get('confidence')})")
                return result
            except json.JSONDecodeError:
                return {
                    "issue_type": None,
                    "confidence": 0,
                    "reasoning": "AI response format error",
                    "raw_response": response
                }
                
        except Exception as e:
            logger.error(f"AI issue understanding failed: {e}")
            return {
                "issue_type": None,
                "confidence": 0,
                "reasoning": f"AI error: {str(e)}"
            }

# Global instance for use in the main app
ai_speech_intelligence = None

def initialize_ai_speech_intelligence():
    """Initialize the global AI speech intelligence system"""
    global ai_speech_intelligence
    try:
        ai_speech_intelligence = AIAddressIntelligence()
        return True
    except Exception as e:
        logger.error(f"Failed to initialize AI Speech Intelligence: {e}")
        return False

if __name__ == "__main__":
    # Test the AI system
    ai = AIAddressIntelligence()
    
    test_inputs = [
        "2540 port richmond avenue",
        "290 port richmond", 
        "1220 targee street",
        "my washing machine is broken",
        "I have no power in my apartment"
    ]
    
    for test_input in test_inputs:
        print(f"\n🧠 Testing: '{test_input}'")
        
        # Test address understanding
        address_result = ai.understand_address_intent(test_input)
        print(f"   Address: {address_result}")
        
        # Test issue understanding  
        issue_result = ai.understand_maintenance_issue(test_input)
        print(f"   Issue: {issue_result}")