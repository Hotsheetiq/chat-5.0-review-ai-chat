#!/usr/bin/env python3
import requests

def test_intelligent_chris():
    """Test the new intelligent Chris with time-based greetings"""
    
    webhook_url = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/voice"
    
    try:
        response = requests.post(webhook_url, 
                               data={'CallSid': 'test_intelligent_chris', 'From': '+15551234567'}, 
                               timeout=8, verify=False)
        
        print(f"Intelligent Chris test - Status: {response.status_code}")
        print(f"Time-based greeting: {'Good evening' in response.text or 'Good morning' in response.text or 'Good afternoon' in response.text}")
        print(f"ElevenLabs active: {'<Play>' in response.text}")
        
        if response.status_code == 200:
            print("✅ Intelligent Chris with time greetings working!")
            return True
        else:
            print("❌ Issue with intelligent Chris")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_intelligent_chris()