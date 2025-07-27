"""
Background AI Processing with Hold Messages
Handles concurrent AI processing while playing hold audio
"""

import asyncio
import logging
import threading
import time
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor, Future
import uuid

# Global processing storage
processing_tasks: Dict[str, Dict[str, Any]] = {}
executor = ThreadPoolExecutor(max_workers=10)

def start_background_processing(call_sid: str, speech_text: str, conversation_history: list, 
                              ai_function, *args, **kwargs) -> str:
    """
    Start AI processing in background and return processing ID
    """
    processing_id = f"proc_{uuid.uuid4().hex[:8]}"
    
    # Submit AI task to background thread
    future = executor.submit(ai_function, speech_text, conversation_history, *args, **kwargs)
    
    processing_tasks[call_sid] = {
        'processing_id': processing_id,
        'future': future,
        'speech_text': speech_text,
        'start_time': time.time(),
        'status': 'processing'
    }
    
    logging.info(f"🚀 BACKGROUND PROCESSING STARTED: {processing_id} for call {call_sid}")
    return processing_id

def get_processing_result(call_sid: str, timeout: float = 4.0) -> Optional[str]:
    """
    Get result from background processing, wait up to timeout seconds
    """
    if call_sid not in processing_tasks:
        logging.warning(f"❌ No processing task found for call {call_sid}")
        return None
    
    task_info = processing_tasks[call_sid]
    future = task_info['future']
    
    try:
        # Wait for result with timeout
        result = future.result(timeout=timeout)
        task_info['status'] = 'completed'
        task_info['result'] = result
        
        elapsed = time.time() - task_info['start_time']
        logging.info(f"✅ BACKGROUND PROCESSING COMPLETED: {task_info['processing_id']} in {elapsed:.2f}s")
        
        return result
        
    except Exception as e:
        task_info['status'] = 'error'
        task_info['error'] = str(e)
        logging.error(f"❌ BACKGROUND PROCESSING ERROR: {task_info['processing_id']} - {e}")
        return None

def cleanup_processing_task(call_sid: str):
    """Clean up completed processing task"""
    if call_sid in processing_tasks:
        del processing_tasks[call_sid]
        logging.info(f"🧹 CLEANED UP processing task for call {call_sid}")

def generate_hold_audio_url() -> str:
    """Generate hold message audio URL"""
    # This should be a pre-recorded ElevenLabs audio file
    return "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/static/please_hold.mp3"

def create_hold_twiml(call_sid: str, processing_id: str) -> str:
    """
    Create TwiML that plays hold message while AI processes
    """
    hold_audio_url = generate_hold_audio_url()
    
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{hold_audio_url}</Play>
    <Redirect>/get-result/{call_sid}</Redirect>
</Response>'''

def create_result_twiml(response_text: str, call_sid: str) -> str:
    """
    Create TwiML with AI response result
    """
    from elevenlabs_integration import generate_audio_url
    
    try:
        audio_url = generate_audio_url(response_text)
        
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Play>{audio_url}</Play>
    <Gather input="speech dtmf" timeout="8" speechTimeout="4" dtmfTimeout="2" language="en-US" action="/handle-input/{call_sid}" method="POST">
    </Gather>
    <Redirect>/handle-speech/{call_sid}</Redirect>
</Response>'''
    
    except Exception as e:
        logging.error(f"❌ Error generating result TwiML: {e}")
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Matthew-Neural">I'm sorry, there was a technical issue. Please try again.</Say>
    <Gather input="speech dtmf" timeout="8" speechTimeout="4" dtmfTimeout="2" language="en-US" action="/handle-input/{call_sid}" method="POST">
    </Gather>
    <Redirect>/handle-speech/{call_sid}</Redirect>
</Response>'''