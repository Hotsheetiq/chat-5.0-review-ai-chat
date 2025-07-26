#!/usr/bin/env python3
"""
Test specifically for address confirmation fix:
- "26 Port Richmond Avenue" should trigger "Did you mean 29 Port Richmond Avenue?"
- "64 Port Richmond Avenue" should trigger "Did you mean 29 Port Richmond Avenue?"
- This should happen BEFORE speech corrections convert the invalid address to valid
"""

import requests
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_address_confirmation():
    """Test that invalid addresses trigger confirmation prompts"""
    print("🎯 TESTING ADDRESS CONFIRMATION SYSTEM")
    print("Testing that Chris asks 'Did you mean 29 Port Richmond Avenue?' for invalid addresses")
    
    session = requests.Session()
    base_url = "http://localhost:5000"
    
    test_cases = [
        ("26 port richmond avenue washing machine", "Should ask 'Did you mean 29 Port Richmond Avenue?'"),
        ("64 port richmond avenue electrical problem", "Should ask 'Did you mean 29 Port Richmond Avenue?'"),
        ("6 port richmond avenue plumbing issue", "Should ask 'Did you mean 29 Port Richmond Avenue?'"),
        ("washing machine 24 port richmond", "Should ask 'Did you mean 29 Port Richmond Avenue?'"),
    ]
    
    for i, (test_input, expected) in enumerate(test_cases):
        print(f"\n{'='*60}")
        print(f"🧪 TEST {i+1}: {test_input}")
        print(f"🎯 Expected: {expected}")
        print(f"{'='*60}")
        
        call_sid = f"test_address_{int(time.time())}_{i}"
        
        try:
            response = session.post(f"{base_url}/handle-input/{call_sid}", data={
                'SpeechResult': test_input,
                'From': '+15551234567',
                'CallSid': call_sid
            })
            
            if response.status_code == 200:
                response_text = response.text
                
                # Check for address confirmation patterns
                if "I heard" in response_text and "Did you mean" in response_text and "29 Port Richmond Avenue" in response_text:
                    print("✅ ADDRESS CONFIRMATION WORKING: Chris asks for confirmation")
                    print(f"📞 Response contains: 'Did you mean 29 Port Richmond Avenue?'")
                elif "service ticket" in response_text.lower():
                    print("❌ ADDRESS CONFIRMATION FAILED: Chris created ticket without asking for confirmation")
                    print(f"📞 Response: Created service ticket (should have asked for confirmation first)")
                else:
                    print("ℹ️ Other response type - checking content...")
                    if "29" in response_text:
                        print("ℹ️ Contains '29' - may be working")
                    else:
                        print("❌ No address confirmation detected")
                        
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test Error: {e}")
        
        time.sleep(1)  # Pause between tests

def test_sms_functionality():
    """Test SMS system with a valid phone number"""
    print(f"\n{'='*60}")
    print("📱 TESTING SMS SYSTEM")
    print("Testing SMS confirmation for service tickets")
    print(f"{'='*60}")
    
    session = requests.Session()
    base_url = "http://localhost:5000"
    call_sid = f"test_sms_{int(time.time())}"
    
    # Step 1: Create a service ticket first
    print("\n📞 Step 1: Creating service ticket...")
    response1 = session.post(f"{base_url}/handle-input/{call_sid}", data={
        'SpeechResult': 'washing machine broken at 29 port richmond avenue',
        'From': '+15551234567',  # Valid phone number format
        'CallSid': call_sid
    })
    
    if "service ticket" in response1.text.lower():
        print("✅ Service ticket created successfully")
        
        # Step 2: Request SMS confirmation
        print("\n📱 Step 2: Requesting SMS confirmation...")
        time.sleep(1)
        
        response2 = session.post(f"{base_url}/handle-input/{call_sid}", data={
            'SpeechResult': 'yes text me the details',
            'From': '+15551234567',
            'CallSid': call_sid
        })
        
        if response2.status_code == 200:
            response_text = response2.text
            if "texted you" in response_text.lower() or "text" in response_text.lower():
                print("✅ SMS CONFIRMATION: Chris acknowledges sending text")
            elif "system error" in response_text.lower():
                print("❌ SMS SYSTEM ERROR: Still showing system error")
            else:
                print("ℹ️ SMS response received, checking content...")
        else:
            print(f"❌ SMS request failed with status: {response2.status_code}")
    else:
        print("❌ Service ticket creation failed - cannot test SMS")

if __name__ == "__main__":
    test_address_confirmation()
    test_sms_functionality()
    
    print(f"\n{'='*60}")
    print("🎯 CRITICAL TESTS SUMMARY:")
    print("1. Address Confirmation: Chris should ask 'Did you mean 29 Port Richmond Avenue?' for invalid addresses")
    print("2. SMS System: Chris should send text confirmations without 'system error'")
    print("3. Both fixes ensure professional customer service experience")
    print(f"{'='*60}")