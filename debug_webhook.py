#!/usr/bin/env python3
"""
Debug script to help identify Twilio webhook issues
"""

import requests
import os

def test_webhook_endpoints():
    """Test all webhook endpoints to ensure they're working"""
    base_url = "http://localhost:5000"
    
    print("🔍 Testing webhook endpoints...")
    
    # Test 1: Incoming call endpoint
    print("\n1. Testing /voice endpoint (incoming call):")
    response = requests.post(f"{base_url}/voice", data={
        "CallSid": "debug_call_123",
        "From": "+15551234567",
        "To": "+18886411102"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # Test 2: Speech handling endpoint
    print("\n2. Testing /handle-speech endpoint:")
    response = requests.post(f"{base_url}/handle-speech/debug_call_123", data={
        "SpeechResult": "hello chris",
        "From": "+15551234567"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # Test 3: Maintenance request flow
    print("\n3. Testing maintenance request flow:")
    response = requests.post(f"{base_url}/handle-speech/debug_call_123", data={
        "SpeechResult": "electrical problem",
        "From": "+15551234567"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
    
    # Test 4: Address handling
    print("\n4. Testing address handling:")
    response = requests.post(f"{base_url}/handle-speech/debug_call_123", data={
        "SpeechResult": "122 Targee Street",
        "From": "+15551234567"
    })
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")

def check_twilio_webhook_url():
    """Check what webhook URL should be configured in Twilio"""
    repl_slug = os.environ.get('REPL_SLUG')
    repl_owner = os.environ.get('REPL_OWNER')
    
    if repl_slug and repl_owner:
        webhook_url = f"https://{repl_slug}.{repl_owner}.replit.app/voice"
        print(f"\n🌐 Your Twilio webhook URL should be:")
        print(f"   {webhook_url}")
        print(f"\n📝 Make sure this URL is configured in your Twilio phone number settings")
    else:
        print("\n❌ Could not determine Replit app URL")
        print("   Check REPL_SLUG and REPL_OWNER environment variables")

if __name__ == "__main__":
    print("🔧 Chris Voice Assistant - Webhook Debug Tool")
    print("=" * 50)
    
    test_webhook_endpoints()
    check_twilio_webhook_url()
    
    print("\n✅ Debug complete!")
    print("\nIf all tests show Status: 200, the issue is likely:")
    print("1. Twilio webhook URL configuration")
    print("2. Network connectivity to Replit")
    print("3. Phone number configuration in Twilio console")