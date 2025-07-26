import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class GrokAI:
    """Grok AI integration for enhanced conversation memory and faster responses"""
    
    def __init__(self):
        self.api_key = os.environ.get("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable is required")
        
        # Create Grok client using OpenAI-compatible API
        self.client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=self.api_key
        )
        logger.info("✅ Grok AI client initialized successfully")
    
    def generate_response(self, messages, max_tokens=200, temperature=0.7, timeout=2.0):
        """Generate response using Grok with enhanced conversation memory"""
        try:
            response = self.client.chat.completions.create(
                model="grok-2-1212",  # Latest Grok model for text processing
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Grok API error: {e}")
            raise
    
    def analyze_conversation_context(self, conversation_history):
        """Analyze conversation for better context understanding"""
        try:
            # Build context analysis prompt
            context_messages = [
                {
                    "role": "system",
                    "content": "Analyze this conversation and identify: 1) What issues/problems were mentioned 2) What addresses were discussed 3) What the caller needs. Respond in JSON format."
                }
            ]
            
            # Add conversation history
            for entry in conversation_history[-6:]:  # Last 6 messages for context
                context_messages.append({
                    "role": entry.get('role', 'user'),
                    "content": entry.get('content', '')
                })
            
            response = self.client.chat.completions.create(
                model="grok-2-1212",
                messages=context_messages,
                max_tokens=150,
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.warning(f"Context analysis failed: {e}")
            return {}