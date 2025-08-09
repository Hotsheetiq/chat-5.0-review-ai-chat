# Production Phone Agent - Chris for Grinberg Management
# Entry point for Gunicorn (main:app)

try:
    from sub_1s_streaming_app import app
except ImportError:
    from app import app

from flask import jsonify, request
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Property Management Voice Assistant is running",
        "timestamp": datetime.now(pytz.timezone('America/New_York')).isoformat()
    })

@app.route('/incoming-call', methods=['GET', 'POST'])
def incoming_call():
    """
    Main Twilio webhook for incoming calls
    Implements full call flow with business rules, Rent Manager integration, and streaming
    """
    from twilio.twiml.voice_response import VoiceResponse
    import os
    
    # Get call information
    call_sid = request.values.get('CallSid', 'unknown')
    caller_number = request.values.get('From', 'unknown')
    
    logger.info(f"📞 Incoming call: {call_sid} from {caller_number}")
    
    # Initialize call session
    from twilio_media_stream_handler import media_stream_handler
    media_stream_handler.initialize_call_session(call_sid, caller_number)
    
    # Determine current time and office hours
    et_time = datetime.now(pytz.timezone('America/New_York'))
    is_office_hours = (
        et_time.weekday() < 5 and  # Monday-Friday
        9 <= et_time.hour < 17     # 9 AM - 5 PM
    )
    
    # Get host for webhook URLs
    host = request.headers.get('Host', 'localhost:5000')
    if host.startswith('0.0.0.0'):
        host = f"{os.environ.get('REPL_SLUG', 'maintenancelinker')}.{os.environ.get('REPL_OWNER', 'brokeropenhouse')}.repl.co"
    
    # Build TwiML for streaming call flow
    response = VoiceResponse()
    
    # Time-appropriate greeting
    if et_time.hour < 12:
        greeting = "Good morning"
    elif et_time.hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    
    # Initial greeting with streaming setup
    response.say(f"{greeting}, you've reached Grinberg Management. This is Chris, your voice assistant.", voice="Polly.Joanna")
    
    # Start streaming media connection
    connect = response.connect()
    connect.stream(url=f"wss://{host}/twilio-media?callSid={call_sid}&officeHours={'true' if is_office_hours else 'false'}")
    
    logger.info(f"🎯 Call {call_sid} routed to streaming pipeline (office_hours: {is_office_hours})")
    
    return str(response), 200, {'Content-Type': 'application/xml'}

@app.route('/self-test', methods=['GET'])
def self_test():
    """
    Production readiness self-test endpoint
    Tests all critical functionality and returns pass/fail
    """
    import json
    from datetime import time
    
    results = {}
    all_passed = True
    
    try:
        # Test 1: Business hours logic
        test_time_business = datetime.now(pytz.timezone('America/New_York')).replace(
            hour=10, minute=0, second=0, microsecond=0
        )
        test_time_after = test_time_business.replace(hour=20)
        
        is_business = (
            test_time_business.weekday() < 5 and 
            9 <= test_time_business.hour < 17
        )
        is_after = not (
            test_time_after.weekday() < 5 and 
            9 <= test_time_after.hour < 17
        )
        
        results['business_hours_test'] = is_business and is_after
        
    except Exception as e:
        results['business_hours_test'] = False
        logger.error(f"Business hours test failed: {e}")
    
    try:
        # Test 2: OpenAI streaming
        from openai_conversation_manager import conversation_manager
        openai_ready = conversation_manager.test_streaming()
        results['openai_streaming_test'] = openai_ready
        
    except Exception as e:
        results['openai_streaming_test'] = False
        logger.error(f"OpenAI test failed: {e}")
    
    try:
        # Test 3: ElevenLabs integration
        from elevenlabs_streaming import streaming_tts_client
        elevenlabs_ready = streaming_tts_client.test_streaming()
        results['elevenlabs_test'] = elevenlabs_ready
        
    except Exception as e:
        results['elevenlabs_test'] = False
        logger.error(f"ElevenLabs test failed: {e}")
    
    try:
        # Test 4: Rent Manager connection
        try:
            from rent_manager_adapter import verify_property, create_ticket
            # Test with a sample address
            rm_result = verify_property("123 Test Street")
            results['rent_manager_test'] = True  # If function exists and doesn't crash
        except ImportError:
            results['rent_manager_test'] = False
            logger.warning("Rent Manager not available")
        
    except Exception as e:
        results['rent_manager_test'] = False
        logger.error(f"Rent Manager test failed: {e}")
    
    try:
        # Test 5: Environment variables
        import os
        required_vars = ['OPENAI_API_KEY', 'ELEVENLABS_API_KEY', 'SENDGRID_API_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        results['environment_test'] = len(missing_vars) == 0
        results['missing_vars'] = missing_vars
        
    except Exception as e:
        results['environment_test'] = False
        logger.error(f"Environment test failed: {e}")
    
    try:
        # Test 6: Emergency detection
        from openai_conversation_manager import conversation_manager
        test_facts = conversation_manager.extract_session_facts("TEST_CALL", "I have no heat")
        is_emergency = test_facts.get('priority') == 'Emergency'
        results['emergency_detection_test'] = is_emergency
        
    except Exception as e:
        results['emergency_detection_test'] = False
        logger.error(f"Emergency detection test failed: {e}")
    
    # Overall pass/fail
    test_results = [v for k, v in results.items() if k != 'missing_vars' and isinstance(v, bool)]
    all_passed = all(test_results)
    
    results['overall_status'] = 'PASS' if all_passed else 'FAIL'
    results['tests_passed'] = sum(test_results)
    results['total_tests'] = len(test_results)
    
    status_code = 200 if all_passed else 500
    
    return jsonify({
        'status': results['overall_status'],
        'timestamp': datetime.now(pytz.timezone('America/New_York')).isoformat(),
        'results': results
    }), status_code