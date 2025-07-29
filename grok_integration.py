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
                model="grok-4-0709",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
                temperature=0.1
            )
            logger.info("🚀 Grok 4.0 pre-warmed - first responses will be faster")
        except Exception as e:
            logger.warning(f"Pre-warm failed (non-critical): {e}")
    
    def generate_response(self, messages, max_tokens=100, temperature=0.5, timeout=4.0):
        """Generate response using Grok 4.0 as default with Grok 2 fallback"""
        try:
            # 🛡️ CONSTRAINT PROTECTION: ALWAYS USE GROK 4.0 AS PRIMARY (User Required)
            # Use Grok 4.0 as primary model - more advanced reasoning and conversation quality
            try:
                response = self.client.chat.completions.create(
                    model="grok-4-0709",  # 🛡️ CONSTRAINT: ALWAYS Grok 4.0 primary
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout
                )
                content = response.choices[0].message.content
                logger.info(f"✅ Using Grok 4.0 - primary model (CONSTRAINT PROTECTED) - Response length: {len(content) if content else 0}")
                
                # Enhanced debugging for empty responses
                if not content or len(content.strip()) == 0:
                    logger.error(f"❌ GROK 4.0 EMPTY RESPONSE DEBUG:")
                    logger.error(f"  Raw content: {repr(content)}")
                    logger.error(f"  Response ID: {getattr(response, 'id', 'unknown')}")
                    logger.error(f"  Model used: {getattr(response, 'model', 'unknown')}")
                    logger.error(f"  Usage: {getattr(response, 'usage', 'unknown')}")
                    # Don't fallback for empty responses - this is the core issue
                    return "I understand you're having an issue. Can you tell me more details about what's happening so I can help you properly?"
                
                return content.strip()
                
            except Exception as e:
                # Only fallback to Grok 2 for connection/API errors, not empty responses
                logger.error(f"Grok 4.0 connection/API error: {e}")
                try:
                    response = self.client.chat.completions.create(
                        model="grok-2-1212",  # Emergency fallback only for API errors
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=max(2.0, timeout - 1.0)
                    )
                    content = response.choices[0].message.content
                    if content and len(content.strip()) > 0:
                        logger.warning("⚠️ Using Grok 2 emergency fallback due to API error")
                        return content.strip()
                    else:
                        logger.error("❌ Grok 2 also returned empty response")
                        return "I'm here to help with your concern. What's the issue you're experiencing?"
                except Exception as e2:
                    logger.error(f"All Grok models failed: {e}, {e2}")
                    return "I understand you need assistance. Can you describe what's happening?"
            
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