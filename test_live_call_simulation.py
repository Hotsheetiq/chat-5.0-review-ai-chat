#!/usr/bin/env python3
"""
Test that simulates actual Twilio call flow to debug address confirmation
"""

import requests
import time

def test_live_address_confirmation():
    """Test address confirmation with actual webhook flow"""
    print("🎯 TESTING LIVE ADDRESS CONFIRMATION")
    print("Simulating real Twilio webhook calls...")
    
    base_url = "http://localhost:5000"
    call_sid = f"CA{int(time.time())}"  # Realistic CallSid format
    
    # Step 1: Incoming call
    print("\n📞 Step 1: Incoming call webhook...")
    incoming_response = requests.post(f"{base_url}/webhook", data={
        'CallSid': call_sid,
        'From': '+15551234567',
        'To': '+18886411102'
    })
    
    print(f"Incoming call status: {incoming_response.status_code}")
    
    # Step 2: User says invalid address with appliance issue
    print("\n📞 Step 2: User says '26 port richmond avenue washing machine'...")
    speech_response = requests.post(f"{base_url}/handle-input/{call_sid}", data={
        'SpeechResult': '26 port richmond avenue washing machine',
        'From': '+15551234567',
        'CallSid': call_sid,
        'Confidence': '0.8'
    })
    
    print(f"Speech response status: {speech_response.status_code}")
    response_text = speech_response.text
    
    # Check for address confirmation
    if "I heard 26 Port Richmond Avenue" in response_text:
        print("✅ ADDRESS CONFIRMATION DETECTED: Chris asks about invalid address")
        if "Did you mean 29 Port Richmond Avenue" in response_text:
            print("✅ CORRECT SUGGESTION: Chris suggests 29 Port Richmond Avenue")
        else:
            print("❌ INCORRECT SUGGESTION: Chris doesn't suggest 29 Port Richmond Avenue")
    elif "service ticket" in response_text.lower():
        print("❌ IMMEDIATE TICKET CREATION: Chris created ticket without asking for confirmation")
    else:
        print("ℹ️ OTHER RESPONSE: Checking content...")
        print(f"Response snippet: {response_text[:200]}...")
    
    return call_sid

def test_live_sms_flow():
    """Test SMS system with live call flow"""
    print(f"\n{'='*60}")
    print("📱 TESTING LIVE SMS FLOW")
    print("Testing SMS after ticket creation...")
    
    base_url = "http://localhost:5000"
    call_sid = f"CA{int(time.time())}"
    
    # Step 1: Create ticket with valid address
    print("\n📞 Step 1: Creating ticket with valid address...")
    requests.post(f"{base_url}/webhook", data={
        'CallSid': call_sid,
        'From': '+15551234567',
        'To': '+18886411102'
    })
    
    time.sleep(1)
    
    # Create service ticket
    ticket_response = requests.post(f"{base_url}/handle-input/{call_sid}", data={
        'SpeechResult': 'washing machine broken at 29 port richmond avenue',
        'From': '+15551234567',
        'CallSid': call_sid,
        'Confidence': '0.9'
    })
    
    print(f"Ticket creation status: {ticket_response.status_code}")
    if "service ticket" in ticket_response.text.lower():
        print("✅ Service ticket created")
        
        # Step 2: Request SMS
        print("\n📱 Step 2: Requesting SMS...")
        time.sleep(2)
        
        sms_response = requests.post(f"{base_url}/handle-input/{call_sid}", data={
            'SpeechResult': 'yes please text me the details',
            'From': '+15551234567',
            'CallSid': call_sid,
            'Confidence': '0.9'
        })
        
        print(f"SMS request status: {sms_response.status_code}")
        sms_text = sms_response.text.lower()
        
        if "system error" in sms_text:
            print("❌ SMS SYSTEM ERROR: Still showing 'system error'")
        elif "texted you" in sms_text or "text you" in sms_text:
            print("✅ SMS SUCCESS: Chris confirms text sent")
        elif "i've created" in sms_text and "dimitry will contact" in sms_text:
            print("⚠️ SMS FALLBACK: Chris provides fallback message")
        else:
            print("ℹ️ OTHER SMS RESPONSE")
            print(f"SMS response snippet: {sms_text[:200]}...")
    else:
        print("❌ Ticket creation failed")

if __name__ == "__main__":
    test_live_address_confirmation()
    test_live_sms_flow()
    
    print(f"\n{'='*60}")
    print("🎯 LIVE TESTING COMPLETE")
    print("This tests the actual webhook flow that Twilio uses")
    print(f"{'='*60}")