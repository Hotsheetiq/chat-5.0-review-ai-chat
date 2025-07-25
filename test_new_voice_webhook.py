#!/usr/bin/env python3
import requests

def test_new_voice_webhook():
    """Test webhook with new voice ID"""
    
    webhook_url = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/voice"
    
    try:
        response = requests.post(webhook_url, 
                               data={'CallSid': 'test_new_voice', 'From': '+15551234567'}, 
                               timeout=10, verify=False)
        
        print(f"Webhook test - Status: {response.status_code}")
        print(f"ElevenLabs active: {'<Play>' in response.text}")
        print(f"Response snippet: {response.text[:150]}...")
        
        if response.status_code == 200 and "<Play>" in response.text:
            print("✅ New voice active in phone system!")
            return True
        else:
            print("❌ Issue with webhook")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_new_voice_webhook()