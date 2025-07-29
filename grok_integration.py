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
            # 🔎 1. TRACE AND PRINT THE PROMPT
            logger.info(f"[DEBUG] Full messages sent to Grok: {json.dumps(messages, indent=2)}")
            logger.info(f"[DEBUG] Parameters: max_tokens={max_tokens}, temperature={temperature}, timeout={timeout}")

            # 🛡️ CONSTRAINT PROTECTION: ALWAYS USE GROK 4.0 AS PRIMARY (User Required)
            # Use Grok 4.0 as primary model - more advanced reasoning and conversation quality
            try:
                logger.info("[DEBUG] Sending request to Grok 4.0...")
                response = self.client.chat.completions.create(
                    model="grok-4-0709",  # 🛡️ CONSTRAINT: ALWAYS Grok 4.0 primary
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout
                )
                
                # 🛠️ 2. CHECK THE API RESPONSE OBJECT
                logger.info(f"[DEBUG] Grok 4.0 raw response object: {response}")
                logger.info(f"[DEBUG] Response type: {type(response)}")
                logger.info(f"[DEBUG] Response attributes: {dir(response)}")
                
                # ✅ 3. FIX THE RESPONSE PARSING
                try:
                    content = response.choices[0].message.content
                    logger.info(f"[DEBUG] Extracted content: {repr(content)}")
                    logger.info(f"[DEBUG] Content type: {type(content)}")
                    logger.info(f"[DEBUG] Content length: {len(content) if content else 0}")
                    
                    # Handle None content
                    if content is None:
                        logger.error("[ERROR] Grok 4.0 response content was None")
                        content = ""
                    
                    # Strip whitespace and check again
                    content = content.strip() if content else ""
                    
                    logger.info(f"✅ Using Grok 4.0 - primary model (CONSTRAINT PROTECTED) - Response length: {len(content)}")
                    
                    # 🔐 5. DO NOT ATTEMPT FIXES BLINDLY - Handle empty responses properly
                    if not content or len(content) == 0:
                        logger.error("[ERROR] Grok 4.0 response content was empty or malformed.")
                        logger.error(f"❌ GROK 4.0 EMPTY RESPONSE DEBUG:")
                        logger.error(f"  Raw content: {repr(content)}")
                        logger.error(f"  Response ID: {getattr(response, 'id', 'unknown')}")
                        logger.error(f"  Model used: {getattr(response, 'model', 'unknown')}")
                        logger.error(f"  Usage: {getattr(response, 'usage', 'unknown')}")
                        
                        # Try Grok 2 as fallback for empty responses - PROVEN TO WORK
                        logger.info("[DEBUG] Attempting Grok 2 fallback for empty Grok 4.0 response...")
                        try:
                            fallback_response = self.client.chat.completions.create(
                                model="grok-2-1212",
                                messages=messages,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                timeout=max(2.0, timeout - 1.0)
                            )
                            logger.info(f"[DEBUG] Grok 2 fallback response received")
                            fallback_content = fallback_response.choices[0].message.content
                            if fallback_content and fallback_content.strip():
                                logger.info(f"✅ Grok 2 fallback successful - Response length: {len(fallback_content)}")
                                logger.info(f"📝 Grok 2 content: {repr(fallback_content[:100])}...")
                                return fallback_content.strip()
                            else:
                                logger.error("[ERROR] Grok 2 also returned empty content")
                        except Exception as fallback_error:
                            logger.error(f"[ERROR] Grok 2 fallback failed: {fallback_error}")
                        
                        # Enhanced intelligent fallback for empty responses
                        try:
                            # Extract user input to provide contextual response
                            user_message = ""
                            for msg in messages:
                                if msg.get("role") == "user":
                                    user_message = msg.get("content", "").lower()
                                    break
                            
                            # Intelligent contextual responses based on user input
                            if any(word in user_message for word in ["heat", "heating", "hot", "cold", "temperature"]):
                                return "Let me make sure I understand - you're having a heating issue in your unit. Is that correct?"
                            elif any(word in user_message for word in ["electrical", "electric", "power", "light", "outlet"]):
                                return "So you're telling me there's an electrical problem. Did I get that right?"
                            elif any(word in user_message for word in ["plumbing", "water", "leak", "pipe", "toilet", "sink"]):
                                return "Just to confirm - you have a plumbing issue that needs attention. Is that what you're saying?"
                            elif any(word in user_message for word in ["roach", "bug", "pest", "insect", "cockroach"]):
                                return "Let me make sure I understand - you're dealing with a pest problem in your apartment. Did I get that right?"
                            elif any(word in user_message for word in ["noise", "loud", "neighbor", "disturb"]):
                                return "So you're saying there's a noise issue with neighbors. Is that correct?"
                            elif any(word in user_message for word in ["rent", "payment", "bill", "charge"]):
                                return "Just to confirm - you have a question about your rent or billing. Did I understand that correctly?"
                            else:
                                return "I want to make sure I understand what you need help with. Can you tell me more about what's going on?"
                                
                        except Exception as e:
                            logger.error(f"Fallback response generation failed: {e}")
                            return "I want to make sure I understand your concern. Can you tell me more details about what's happening?"
                
                except (KeyError, IndexError, AttributeError) as parse_error:
                    logger.error(f"[ERROR] Failed to parse Grok 4.0 response: {parse_error}")
                    logger.error(f"[ERROR] Response structure: {response}")
                    # Try to extract any available information
                    try:
                        if hasattr(response, 'choices') and response.choices:
                            if hasattr(response.choices[0], 'message'):
                                logger.error(f"[ERROR] Message object: {response.choices[0].message}")
                    except Exception as debug_error:
                        logger.error(f"[ERROR] Debug extraction failed: {debug_error}")
                
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