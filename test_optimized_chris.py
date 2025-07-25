#!/usr/bin/env python3
import requests

def test_optimized_chris():
    """Test the optimized Chris system"""
    
    webhook_url = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/voice"
    
    try:
        response = requests.post(webhook_url, 
                               data={'CallSid': 'test_optimized_chris', 'From': '+15551234567'}, 
                               timeout=8, verify=False)
        
        print(f"Optimized Chris test - Status: {response.status_code}")
        print(f"ElevenLabs active: {'<Play>' in response.text}")
        print(f"No extra listening prompts: {response.text.count('listening') == 0}")
        print(f"Response length: {len(response.text)} (faster = shorter)")
        
        if response.status_code == 200:
            print("✅ Optimized Chris working!")
            return True
        else:
            print("❌ Issue with optimization")
            return False
            
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_optimized_chris()