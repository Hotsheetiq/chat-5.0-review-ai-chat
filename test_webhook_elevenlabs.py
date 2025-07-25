#!/usr/bin/env python3
import requests

def test_webhook_with_elevenlabs():
    """Test webhook with ElevenLabs voice generation"""
    
    url = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/voice"
    
    try:
        print("Testing webhook with Pro ElevenLabs...")
        response = requests.post(
            url,
            data={
                'CallSid': 'test_pro_elevenlabs',
                'From': '+15551234567',
                'To': '+18886411102'
            },
            timeout=15,
            verify=False
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}")
        
        if "Play>" in response.text:
            print("✅ ElevenLabs voice detected in response!")
        elif "Say>" in response.text:
            print("⚠️ Still using Polly - may need API key update")
        else:
            print("❌ Unexpected response format")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_webhook_with_elevenlabs()