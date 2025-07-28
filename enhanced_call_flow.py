"""
Enhanced Call Flow System - Immediate Hold Messages with Parallel AI Processing
Implements the exact flow requested: instant hold → parallel AI → queue response → natural timing
"""

import asyncio
import logging
import threading
import time
import os
import uuid
from typing import Optional, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, Future
import requests

logger = logging.getLogger(__name__)

# Global system for managing AI processing
ai_response_queue: Dict[str, Dict[str, Any]] = {}
processing_executor = ThreadPoolExecutor(max_workers=15)
hold_audio_cache = {}

def initialize_hold_audio_cache():
    """Pre-generate and cache hold messages to eliminate ElevenLabs delay"""
    global hold_audio_cache
    
    hold_messages = [
        "Please hold while I check that for you",
        "Let me look into that for you",
        "Please hold while I process your request",
        "Give me just a moment to check on that",
        "Please hold while I gather that information"
    ]
    
    try:
        from elevenlabs_integration import generate_audio_file
        logger.info("🎵 PRE-CACHING HOLD MESSAGES for instant playback...")
        
        for i, message in enumerate(hold_messages):
            try:
                audio_file = generate_audio_file(message)
                hold_audio_cache[f"hold_{i}"] = {
                    'message': message,
                    'audio_file': audio_file,
                    'url': f"/static/{audio_file}"
                }
                logger.info(f"✅ CACHED: {message[:30]}... → {audio_file}")
            except Exception as e:
                logger.warning(f"⚠️ Could not cache hold message {i}: {e}")
                
        logger.info(f"🎵 HOLD AUDIO CACHE READY: {len(hold_audio_cache)} messages cached")
        
    except ImportError:
        logger.warning("⚠️ ElevenLabs not available - using fallback hold messages")
        # Fallback to pre-existing hold audio
        hold_audio_cache['hold_0'] = {
            'message': 'Please hold while I check that for you',
            'audio_file': 'please_hold.mp3',
            'url': '/static/please_hold.mp3'
        }

def get_cached_hold_message() -> str:
    """Get a cached hold message URL instantly"""
    if not hold_audio_cache:
        initialize_hold_audio_cache()
    
    # Return first available cached message
    for key, data in hold_audio_cache.items():
        base_url = os.environ.get('REPLIT_URL', 'https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev')
        return f"{base_url}{data['url']}"
    
    # Ultimate fallback
    return "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/static/please_hold.mp3"

def should_use_enhanced_flow(user_input: str) -> bool:
    """
    Determine if we should use enhanced flow with hold message
    Enhanced flow: instant hold → parallel AI → queued response
    Simple flow: direct instant response
    """
    user_lower = user_input.lower().strip()
    
    # Simple greetings and quick responses - NO hold message needed
    instant_patterns = [
        'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening',
        'thank you', 'thanks', 'yes', 'no', 'okay', 'ok',
        'are you open', 'office hours', 'what time', 'phone number',
        'goodbye', 'bye', 'have a good day'
    ]
    
    # Check for instant response patterns
    if any(pattern in user_lower for pattern in instant_patterns):
        return False
    
    # Short simple questions - NO hold message
    if len(user_input.split()) <= 4 and any(word in user_lower for word in ['what', 'how', 'when', 'where', 'can you']):
        return False
    
    # Complex requests that need AI processing - USE hold message
    complex_patterns = [
        'maintenance', 'repair', 'broken', 'issue', 'problem', 'service', 'fix',
        'apartment', 'unit', 'building', 'address', 'street', 'avenue', 'road',
        'electrical', 'plumbing', 'heating', 'air conditioning', 'appliance',
        'leak', 'water', 'heat', 'cold', 'power', 'light', 'toilet', 'sink',
        'rat', 'mouse', 'pest', 'bug', 'cockroach', 'ant',
        'noise', 'neighbor', 'complaint', 'emergency'
    ]
    
    return any(pattern in user_lower for pattern in complex_patterns) or len(user_input.split()) > 6

def start_parallel_ai_processing(call_sid: str, user_input: str, ai_function: Callable) -> str:
    """
    Start AI processing in parallel immediately when user stops speaking
    Returns processing_id for tracking
    """
    processing_id = f"ai_{uuid.uuid4().hex[:8]}"
    
    logger.info(f"🚀 PARALLEL AI PROCESSING STARTED: {processing_id} for call {call_sid}")
    logger.info(f"📝 INPUT: '{user_input[:60]}...'")
    
    # Submit AI processing to background thread pool
    future = processing_executor.submit(ai_function, user_input)
    
    # Store processing task with metadata
    ai_response_queue[call_sid] = {
        'processing_id': processing_id,
        'future': future,
        'user_input': user_input,
        'start_time': time.time(),
        'status': 'processing',
        'response_ready': False,
        'queued_response': None
    }
    
    # Start monitoring thread to queue response when ready
    monitor_thread = threading.Thread(
        target=_monitor_ai_processing,
        args=(call_sid, processing_id),
        daemon=True
    )
    monitor_thread.start()
    
    return processing_id

def _monitor_ai_processing(call_sid: str, processing_id: str):
    """
    Monitor AI processing and queue response when ready
    Runs in separate thread to avoid blocking
    """
    try:
        if call_sid not in ai_response_queue:
            return
            
        task_info = ai_response_queue[call_sid]
        future = task_info['future']
        
        # Wait for AI processing to complete
        response = future.result(timeout=10.0)  # 10 second max processing time
        
        # Generate TTS audio for the response
        try:
            from fixed_conversation_app import create_voice_response
            voice_response = create_voice_response(response)
            
            # Queue the complete TwiML response
            task_info.update({
                'status': 'completed',
                'response_ready': True,
                'queued_response': voice_response,
                'ai_response_text': response,
                'processing_time': time.time() - task_info['start_time']
            })
            
            logger.info(f"✅ AI RESPONSE QUEUED: {processing_id} in {task_info['processing_time']:.2f}s")
            logger.info(f"🎤 RESPONSE: '{response[:80]}...'")
            
        except Exception as e:
            logger.error(f"❌ TTS generation failed for {processing_id}: {e}")
            # Queue fallback response
            task_info.update({
                'status': 'error',
                'response_ready': True,
                'queued_response': f'<Say voice="Polly.Matthew-Neural">{response}</Say>',
                'ai_response_text': response,
                'processing_time': time.time() - task_info['start_time']
            })
            
    except Exception as e:
        logger.error(f"❌ AI processing failed for {processing_id}: {e}")
        if call_sid in ai_response_queue:
            ai_response_queue[call_sid].update({
                'status': 'error',
                'response_ready': True,
                'queued_response': '<Say voice="Polly.Matthew-Neural">I apologize, there was a technical issue. How can I help you?</Say>',
                'error': str(e)
            })

def create_instant_hold_twiml(call_sid: str) -> str:
    """
    Create TwiML that plays hold message instantly while AI processes in parallel
    This is the FIRST response after user stops speaking
    """
    hold_audio_url = get_cached_hold_message()
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{hold_audio_url}</Play>
    <Redirect>/get-queued-response/{call_sid}</Redirect>
</Response>'''

def get_queued_ai_response(call_sid: str, max_wait: float = 8.0) -> str:
    """
    Get the queued AI response after hold message completes
    Wait for AI processing if it's not done yet
    """
    if call_sid not in ai_response_queue:
        logger.warning(f"❌ No AI processing found for call {call_sid}")
        return create_fallback_response(call_sid)
    
    task_info = ai_response_queue[call_sid]
    processing_id = task_info['processing_id']
    
    logger.info(f"🎯 RETRIEVING QUEUED RESPONSE: {processing_id}")
    
    # Wait for response to be ready
    start_wait = time.time()
    while not task_info.get('response_ready', False):
        if time.time() - start_wait > max_wait:
            logger.warning(f"⏰ TIMEOUT waiting for AI response {processing_id}")
            break
        time.sleep(0.1)  # Check every 100ms
    
    if task_info.get('response_ready', False):
        queued_response = task_info.get('queued_response')
        processing_time = task_info.get('processing_time', 0)
        hold_time = time.time() - task_info['start_time']
        
        logger.info(f"✅ SEAMLESS DELIVERY: AI processed in {processing_time:.2f}s, total flow in {hold_time:.2f}s")
        
        # Clean up
        cleanup_ai_processing(call_sid)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {queued_response}
    <Gather input="speech dtmf" timeout="8" speechTimeout="4" dtmfTimeout="2" language="en-US" action="/handle-input/{call_sid}" method="POST">
    </Gather>
    <Redirect>/handle-speech/{call_sid}</Redirect>
</Response>'''
    
    else:
        # AI processing still not done - return fallback
        logger.warning(f"❌ AI response not ready for {processing_id} - using fallback")
        cleanup_ai_processing(call_sid)
        return create_fallback_response(call_sid)

def create_fallback_response(call_sid: str) -> str:
    """Create fallback response when AI processing fails or times out"""
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew-Neural">I'm processing your request. How can I help you today?</Say>
    <Gather input="speech dtmf" timeout="8" speechTimeout="4" dtmfTimeout="2" language="en-US" action="/handle-input/{call_sid}" method="POST">
    </Gather>
    <Redirect>/handle-speech/{call_sid}</Redirect>
</Response>'''

def cleanup_ai_processing(call_sid: str):
    """Clean up completed AI processing task"""
    if call_sid in ai_response_queue:
        processing_id = ai_response_queue[call_sid].get('processing_id', 'unknown')
        del ai_response_queue[call_sid]
        logger.info(f"🧹 CLEANED UP AI processing: {processing_id}")

def add_enhanced_call_flow_routes(app):
    """Add enhanced call flow routes to Flask app"""
    
    @app.route('/get-queued-response/<call_sid>', methods=['GET', 'POST'])
    def get_queued_response_route(call_sid):
        """Route to get queued AI response after hold message"""
        return get_queued_ai_response(call_sid)
        
    logger.info("✅ ENHANCED CALL FLOW ROUTES ADDED")

# Initialize hold audio cache when module loads
initialize_hold_audio_cache()