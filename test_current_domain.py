#!/usr/bin/env python3
"""
Test if current domain is working for Twilio webhooks
"""
import requests

def test_domain():
    """Test if the current domain responds properly"""
    current_domain = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev"
    
    # Test voice endpoint
    try:
        response = requests.post(
            f"{current_domain}/voice",
            data={"CallSid": "test", "From": "+13477430880"},
            timeout=10
        )
        
        if response.status_code == 200 and "xml" in response.text.lower():
            print(f"✅ Current domain is working: {current_domain}")
            print(f"Response includes TwiML: {len(response.text)} chars")
            return True
        else:
            print(f"❌ Domain not responding properly: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing domain: {e}")
        return False

if __name__ == "__main__":
    test_domain()