import os
import json
import logging
import time
import hashlib
from openai import OpenAI

logger = logging.getLogger(__name__)

class GrokAI:
    """OPTIMIZED Grok 4.0 AI integration with connection reuse and caching"""
    
    def __init__(self):
        """Initialize optimized Grok AI with connection pooling"""
        self.api_key = os.environ.get("XAI_API_KEY")
        if not self.api_key:
            raise ValueError("XAI_API_KEY environment variable is required")
        
        # Create optimized Grok client with connection reuse
        self.client = OpenAI(
            base_url="https://api.x.ai/v1",
            api_key=self.api_key,
            timeout=8.0,  # Optimized timeout
            max_retries=1  # Faster failure for performance
        )
        
        # Response cache for common requests
        self.response_cache = {}
        self.cache_max_size = 50
        
        logger.info("✅ OPTIMIZED Grok AI client initialized with connection pooling")
        
        # PRE-WARM with optimized connection
        try:
            start_time = time.time()
            self.client.chat.completions.create(
                model="grok-4-0709",
                messages=[{"role": "user", "content": "Ready"}],
                max_tokens=3,
                temperature=0.1
            )
            warmup_time = time.time() - start_time
            logger.info(f"🚀 Grok 4.0 pre-warmed in {warmup_time:.3f}s - optimized for speed")
        except Exception as e:
            logger.warning(f"Pre-warm failed (non-critical): {e}")
    
    def _get_cache_key(self, messages, max_tokens, temperature):
        """Generate cache key for request"""
        import hashlib
        content = str(messages) + str(max_tokens) + str(temperature)
        return hashlib.md5(content.encode()).hexdigest()
    
    def _cache_response(self, key, response):
        """Cache response with size limit"""
        if len(self.response_cache) >= self.cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self.response_cache))
            del self.response_cache[oldest_key]
        self.response_cache[key] = response
    
    def _optimize_prompt_length(self, messages):
        """Optimize prompt length for faster processing"""
        optimized = []
        for msg in messages:
            if msg.get("role") == "system":
                # Keep system message but truncate if too long
                content = msg.get("content", "")
                if len(content) > 1000:  # Limit system message length
                    # Keep essential parts
                    essential_parts = []
                    for line in content.split('\n'):
                        if any(keyword in line.upper() for keyword in ['CRITICAL', 'CONSTRAINT', 'IMPORTANT', 'NEVER', 'ALWAYS']):
                            essential_parts.append(line)
                    
                    if essential_parts:
                        content = '\n'.join(essential_parts[:10])  # Max 10 critical lines
                    else:
                        content = content[:800]  # Fallback truncation
                        
                optimized.append({"role": "system", "content": content})
            else:
                # Keep user messages as-is but limit length
                content = msg.get("content", "")[:300]  # Truncate long user messages
                optimized.append({"role": msg.get("role"), "content": content})
        
        return optimized
    
    def generate_response(self, messages, max_tokens=60, temperature=0.5, timeout=2.0):
        """OPTIMIZED response generation with caching and reduced tokens"""
        # ⏰ START GROK TIMING
        grok_start_time = time.time()
        
        try:
            # Check cache first for performance
            cache_key = self._get_cache_key(messages, max_tokens, temperature)
            if cache_key in self.response_cache:
                cached_response = self.response_cache[cache_key]
                cache_time = time.time() - grok_start_time
                logger.info(f"[Timing] Grok cache hit: {cache_time:.3f} seconds")
                return cached_response
            
            # Optimize prompt length to reduce processing time
            optimized_messages = self._optimize_prompt_length(messages)
            
            logger.info(f"[DEBUG] OPTIMIZED Grok 4.0 request: max_tokens={max_tokens}, timeout={timeout}")

            # 🛡️ CONSTRAINT PROTECTION: ALWAYS USE GROK 4.0 AS PRIMARY (User Required)
            try:
                response = self.client.chat.completions.create(
                    model="grok-4-0709",  # 🛡️ CONSTRAINT: ALWAYS Grok 4.0 primary
                    messages=optimized_messages,
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
                    
                    # Log successful response with timing
                    grok_time = time.time() - grok_start_time
                    logger.info(f"[Timing] Grok 4.0 success: {grok_time:.3f} seconds")
                    logger.info(f"✅ Using Grok 4.0 - primary model (CONSTRAINT PROTECTED) - Response length: {len(content)}")
                    
                    # Cache successful response
                    self._cache_response(cache_key, content)
                    
                    # 🔐 5. DO NOT ATTEMPT FIXES BLINDLY - Handle empty responses properly
                    if not content or len(content) == 0:
                        logger.error("[ERROR] Grok 4.0 response content was empty or malformed.")
                        
                        # Try Grok 2 as fallback for empty responses - PROVEN TO WORK
                        logger.info("[DEBUG] Attempting optimized Grok 2 fallback...")
                        try:
                            fallback_response = self.client.chat.completions.create(
                                model="grok-2-1212",
                                messages=optimized_messages,
                                max_tokens=max_tokens,
                                temperature=temperature,
                                timeout=max(2.0, timeout - 1.0)
                            )
                            fallback_content = fallback_response.choices[0].message.content
                            if fallback_content and fallback_content.strip():
                                grok_time = time.time() - grok_start_time
                                logger.info(f"[Timing] Grok 2 fallback: {grok_time:.3f} seconds")
                                
                                # Cache the fallback response
                                self._cache_response(cache_key, fallback_content.strip())
                                return fallback_content.strip()
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