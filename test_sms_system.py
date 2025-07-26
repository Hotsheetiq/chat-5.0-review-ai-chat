#!/usr/bin/env python3
"""
Test SMS system specifically to debug why it's showing system errors
"""

import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sms_workflow():
    """Test complete SMS workflow"""
    print("📱 TESTING SMS SYSTEM WORKFLOW")
    print("Testing end-to-end SMS confirmation system")
    
    session = requests.Session()
    base_url = "http://localhost:5000"
    call_sid = f"test_sms_workflow_{int(time.time())}"
    
    print("\n📞 Step 1: Create service ticket with valid address...")
    response1 = session.post(f"{base_url}/handle-input/{call_sid}", data={
        'SpeechResult': 'washing machine broken at 29 port richmond avenue',
        'From': '+15551234567',  # Valid phone number format
        'CallSid': call_sid
    })
    
    print(f"Response status: {response1.status_code}")
    if "service ticket" in response1.text.lower():
        print("✅ Service ticket created")
        
        # Extract ticket number from response
        import re
        ticket_match = re.search(r'#(SV-\d+)', response1.text)
        if ticket_match:
            ticket_number = ticket_match.group(1)
            print(f"✅ Ticket number extracted: {ticket_number}")
        
        time.sleep(2)  # Give system time to process
        
        print("\n📱 Step 2: Request SMS confirmation...")
        response2 = session.post(f"{base_url}/handle-input/{call_sid}", data={
            'SpeechResult': 'yes please text me',
            'From': '+15551234567',
            'CallSid': call_sid
        })
        
        print(f"SMS Response status: {response2.status_code}")
        response_text = response2.text.lower()
        
        if "system error" in response_text:
            print("❌ SMS SYSTEM ERROR: Still showing 'system error'")
        elif "texted you" in response_text or "text you" in response_text:
            print("✅ SMS SUCCESS: Chris confirms text sent")
        elif "trouble sending" in response_text:
            print("⚠️ SMS WARNING: Chris reports trouble sending text")
        else:
            print("ℹ️ SMS Response received, content unclear")
            
        # Check for specific patterns in response
        if ticket_number and ticket_number in response2.text:
            print(f"✅ Ticket number {ticket_number} mentioned in SMS response")
        
    else:
        print("❌ Service ticket creation failed")

def test_sms_variations():
    """Test different ways users might request SMS"""
    sms_requests = [
        "yes text me",
        "text me the details", 
        "yes please text",
        "send me text",
        "yes send sms"
    ]
    
    print("\n📱 TESTING SMS REQUEST VARIATIONS")
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    for i, sms_request in enumerate(sms_requests):
        print(f"\n--- Test {i+1}: '{sms_request}' ---")
        call_sid = f"test_sms_var_{int(time.time())}_{i}"
        
        # First create a ticket
        session.post(f"{base_url}/handle-input/{call_sid}", data={
            'SpeechResult': 'appliance problem 29 port richmond',
            'From': '+15551234567',
            'CallSid': call_sid
        })
        
        time.sleep(1)
        
        # Then request SMS
        response = session.post(f"{base_url}/handle-input/{call_sid}", data={
            'SpeechResult': sms_request,
            'From': '+15551234567',
            'CallSid': call_sid
        })
        
        if "system error" in response.text.lower():
            print("❌ System error")
        elif "text" in response.text.lower():
            print("✅ SMS response")
        else:
            print("ℹ️ Other response")

if __name__ == "__main__":
    test_sms_workflow()
    test_sms_variations()
    
    print(f"\n{'='*60}")
    print("🎯 SMS TESTING COMPLETE")
    print("Key fixes needed:")
    print("1. ✅ Address confirmation working")
    print("2. 📱 SMS system needs 'system error' fix")
    print(f"{'='*60}")