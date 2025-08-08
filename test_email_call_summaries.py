#!/usr/bin/env python3
"""
Test Email Call Summary System
Tests the new automated email summary system that sends detailed call summaries 
after each call session ends with proper priority labeling
"""

import requests
import json
import time
from datetime import datetime
import pytz

def test_email_call_summaries():
    """Test the automated email call summary system"""
    
    base_url = "http://0.0.0.0:5000"
    
    print("📧 TESTING EMAIL CALL SUMMARY SYSTEM")
    print("Testing: Automated email summaries after call ends")
    print("=" * 70)
    
    # Test different priority scenarios
    test_scenarios = [
        {
            "conversation": [
                "I have no heat in my apartment at 123 Main Street unit 4B",
                "My name is John Smith and my number is 555-1234"
            ],
            "call_sid": "EMAIL_TEST_EMERGENCY_001",
            "expected_priority": "EMERGENCY",
            "test_name": "Emergency: No Heat (Should send EMERGENCY alert)"
        },
        {
            "conversation": [
                "My kitchen sink is leaking",
                "I'm at 456 Oak Ave, my name is Jane Doe, 555-5678"  
            ],
            "call_sid": "EMAIL_TEST_STANDARD_001", 
            "expected_priority": "STANDARD",
            "test_name": "Standard: Kitchen Leak (Should send STANDARD summary)"
        },
        {
            "conversation": [
                "I have an urgent electrical problem",
                "The outlet is sparking. This is urgent!",
                "My address is 789 Pine Street, Bob Wilson, 555-9999"
            ],
            "call_sid": "EMAIL_TEST_URGENT_001",
            "expected_priority": "URGENT", 
            "test_name": "Urgent: Electrical Issue (Should send URGENT summary)"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n{i+1}. {scenario['test_name'].upper()}")
        print("-" * 60)
        
        call_sid = scenario['call_sid']
        
        # Simulate conversation
        for j, message in enumerate(scenario['conversation']):
            print(f"Sending message {j+1}: {message}")
            
            try:
                data = {
                    'SpeechResult': message,
                    'Confidence': '0.95',
                    'CallSid': call_sid,
                    'From': '+15551234567'
                }
                
                response = requests.post(f"{base_url}/handle-speech/{call_sid}", 
                                       data=data, timeout=15)
                
                if response.status_code == 200:
                    print(f"  ✅ Message {j+1} processed successfully")
                else:
                    print(f"  ❌ Message {j+1} failed: {response.status_code}")
                    
                time.sleep(1)  # Brief pause between messages
                
            except Exception as e:
                print(f"  ❌ Error sending message {j+1}: {e}")
        
        # Simulate call end to trigger email summary
        print(f"\nTriggering call end for {call_sid}...")
        try:
            end_response = requests.post(f"{base_url}/call-end/{call_sid}", timeout=10)
            
            if end_response.status_code == 200:
                print(f"✅ Call end processed - Email summary should be sent")
                print(f"   Expected priority: {scenario['expected_priority']}")
            else:
                print(f"❌ Call end failed: {end_response.status_code}")
                
        except Exception as e:
            print(f"❌ Error triggering call end: {e}")
        
        print(f"Waiting 3 seconds before next test...")
        time.sleep(3)
    
    print("\n" + "=" * 70)
    print("📧 EMAIL CALL SUMMARY TESTS COMPLETE")
    print("\nCheck your email (configured OWNER_EMAIL) for:")
    print("- [EMERGENCY] 123 Main Street unit 4B — No heat — No Ticket")
    print("- [STANDARD] 456 Oak Ave — Kitchen sink leaking — No Ticket") 
    print("- [URGENT] 789 Pine Street — Electrical problem — No Ticket")
    print("\nEmails should include comprehensive call details, priority labeling,")
    print("contact information, and conversation transcripts.")

def test_email_system_directly():
    """Test the email system directly without full conversation"""
    
    print("\n📧 TESTING EMAIL SYSTEM DIRECTLY")
    print("=" * 50)
    
    base_url = "http://0.0.0.0:5000"
    
    try:
        response = requests.post(f"{base_url}/test-email", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Direct email test result: {result}")
            
            if result.get('status') == 'success':
                print("✅ Email system working properly")
            else:
                print(f"❌ Email system issue: {result.get('message')}")
        else:
            print(f"❌ Email test endpoint failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing email system: {e}")

if __name__ == "__main__":
    # Test email system first
    test_email_system_directly()
    
    # Then test full call summary flow
    test_email_call_summaries()
    
    print("\n🎉 ALL EMAIL TESTS COMPLETE")
    print("Check email logs in the application console for send confirmation.")