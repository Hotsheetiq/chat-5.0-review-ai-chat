#!/usr/bin/env python3
import requests
import json

def test_webhook():
    # Test the correct Replit domain URL
    urls = [
        'https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/voice'
    ]
    
    for url in urls:
        print(f"Testing: {url}")
        try:
            response = requests.post(
                url,
                data={
                    'CallSid': 'test_call_external',
                    'From': '+15551234567',
                    'To': '+18886411102'
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=15,
                verify=False  # Skip SSL verification for testing
            )
            
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Response: {response.text[:500]}")
            
            if response.status_code == 200 and '<?xml' in response.text:
                print("✅ Webhook working correctly!")
                return True
            else:
                print("❌ Webhook response issues")
                
        except Exception as e:
            print(f"Error: {e}")
    
    return False

if __name__ == "__main__":
    test_webhook()