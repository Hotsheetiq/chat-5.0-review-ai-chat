import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class GrokAI:
    """Grok 4.0 AI integration - xAI's flagship model with superior conversation memory and intelligence"""
    
    def __init__(self):
        """Initialize Grok AI with pre-warming to reduce first-response latency"""
        self.api_key = os.environ.get("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable is required")
        
        # Create Grok client using OpenAI-compatible API
        self.client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=self.api_key
        )
        logger.info("✅ Grok AI client initialized successfully")
        
        # PRE-WARM: Make a quick test call to reduce first-response latency
        try:
            self.client.chat.completions.create(
                model="grok-2-1212",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                temperature=0.1
            )
            logger.info("🚀 Grok AI pre-warmed - first responses will be faster")
        except Exception as e:
            logger.warning(f"Pre-warm failed (non-critical): {e}")
    
    def generate_response(self, messages, max_tokens=100, temperature=0.5, timeout=0.6):
        """Generate fast response using optimized Grok settings"""
        try:
            # Use Grok 2 for speed - it's faster than Grok 4.0 with similar quality
            try:
                response = self.client.chat.completions.create(
                    model="grok-2-1212",  # Grok 2 - faster and more reliable
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout  # Fast timeout for speed
                )
                logger.info("✅ Using Grok 2 - optimized for speed")
                return response.choices[0].message.content.strip()
            except Exception as e:
                # If Grok 2 fails, try Grok 4.0 as backup
                logger.warning(f"Grok 2 failed ({e}), trying Grok 4.0")
                response = self.client.chat.completions.create(
                    model="grok-4-0709",  # Backup Grok 4.0
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout + 0.2  # Slightly longer timeout for Grok 4.0
                )
                logger.info("✅ Using Grok 4.0 as backup")
                return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"All Grok models failed: {e}")
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
            
            # Try Grok 4.0 first, fallback to Grok 2 for context analysis
            try:
                response = self.client.chat.completions.create(
                    model="grok-4-0709",  # Grok 4.0 for enhanced context analysis
                    messages=context_messages,
                    max_tokens=150,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            except Exception:
                response = self.client.chat.completions.create(
                    model="grok-2-1212",  # Fallback to Grok 2
                    messages=context_messages,
                    max_tokens=150,
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.warning(f"Context analysis failed: {e}")
            return {}