"""
Simple background processing with hold messages
Adds "Please hold" messages without rewriting the entire conversation system
"""

import logging
import time
from flask import request
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# Global processing tasks
processing_tasks = {}

def should_use_hold_message(user_input: str) -> bool:
    """Determine if this request should use a hold message"""
    user_lower = user_input.lower().strip()
    
    # Skip hold messages for simple/instant responses
    simple_patterns = [
        "hello", "hi", "hey", "yes", "no", "thank you", "thanks",
        "are you open", "office hours", "goodbye", "bye"
    ]
    
    if any(pattern in user_lower for pattern in simple_patterns):
        return False
    
    # Use hold messages for complex requests
    complex_patterns = [
        "I have", "problem", "issue", "broken", "not working",
        "maintenance", "service", "repair", "fix", "create ticket"
    ]
    
    return any(pattern in user_lower for pattern in complex_patterns)

def create_hold_response(call_sid: str) -> str:
    """Create TwiML response with hold message"""
    hold_audio_url = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/static/please_hold.mp3"
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{hold_audio_url}</Play>
    <Redirect>/continue-processing/{call_sid}</Redirect>
</Response>'''

def add_hold_processing_route(app, original_handle_function):
    """Add background processing route to the Flask app"""
    
    @app.route('/continue-processing/<call_sid>', methods=['GET', 'POST'])
    def continue_processing(call_sid):
        """Continue processing after hold message"""
        try:
            # Get the original user input from conversation history or request
            user_input = ""
            caller_phone = ""
            
            # Try to get from conversation history
            from fixed_conversation_app import conversation_history
            if call_sid in conversation_history and conversation_history[call_sid]:
                last_entry = conversation_history[call_sid][-1]
                user_input = last_entry.get('content', '')
                caller_phone = last_entry.get('phone', '')
            
            if not user_input:
                # Fallback: get from request
                user_input = request.values.get('SpeechResult', '')
                caller_phone = request.values.get('From', '')
            
            logger.info(f"🔄 CONTINUING PROCESSING: {call_sid} - '{user_input[:50]}...'")
            
            # Process the request normally
            result = original_handle_function(call_sid, user_input, caller_phone, "")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Continue processing error: {e}")
            
            # Emergency fallback
            return f'''<?xml version="1.0" encoding="UTF-8"?>
            <Response>
                <Say voice="Polly.Matthew-Neural">I'm sorry, there was a technical issue. How can I help you?</Say>
                <Gather input="speech dtmf" timeout="8" speechTimeout="4" dtmфTimeout="2" language="en-US" action="/handle-input/{call_sid}" method="POST">
                </Gather>
                <Redirect>/handle-speech/{call_sid}</Redirect>
            </Response>'''

def wrap_with_hold_processing(original_function):
    """Wrap the original function to add hold message support"""
    
    def wrapped_function(call_sid, user_input, caller_phone, speech_confidence):
        try:
            # Check if we should use hold message
            if should_use_hold_message(user_input):
                logger.info(f"🔄 USING HOLD MESSAGE for: '{user_input[:50]}...'")
                
                # Store processing info
                processing_tasks[call_sid] = {
                    'user_input': user_input,
                    'caller_phone': caller_phone,
                    'speech_confidence': speech_confidence,
                    'start_time': time.time()
                }
                
                # Return hold message TwiML
                return create_hold_response(call_sid)
            else:
                # Process immediately for simple requests
                logger.info(f"⚡ INSTANT PROCESSING for: '{user_input[:50]}...'")
                return original_function(call_sid, user_input, caller_phone, speech_confidence)
                
        except Exception as e:
            logger.error(f"❌ Hold processing wrapper error: {e}")
            # Fall back to original function
            return original_function(call_sid, user_input, caller_phone, speech_confidence)
    
    return wrapped_function