#!/usr/bin/env python3
import requests

def test_after_webhook_update():
    """Test webhook functionality after Twilio URL update"""
    
    url = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/voice"
    
    print("Testing webhook after Twilio update...")
    
    try:
        response = requests.post(url, 
                               data={'CallSid': 'post_update_test', 'From': '+15551234567'}, 
                               timeout=10, verify=False)
        
        print(f"Status: {response.status_code}")
        print(f"ElevenLabs Active: {'<Play>' in response.text}")
        print(f"Valid TwiML: {'<?xml' in response.text}")
        
        if response.status_code == 200 and "<Play>" in response.text:
            print("✅ WEBHOOK PERFECT - Application error should be resolved!")
            print("✅ ElevenLabs voice active - No more Polly!")
            return True
        else:
            print("❌ Issue detected in webhook response")
            print(f"Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_after_webhook_update()