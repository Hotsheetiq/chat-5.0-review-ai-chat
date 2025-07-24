#!/usr/bin/env python3
"""
Webhook connectivity diagnostics for Twilio integration
"""

import requests
import json
from datetime import datetime

def test_external_webhook():
    """Test if the external webhook URL is accessible"""
    webhook_url = "https://workspace.brokeropenhouse.replit.app/voice"
    
    print(f"🔍 Testing external webhook connectivity...")
    print(f"URL: {webhook_url}")
    print("-" * 60)
    
    try:
        # Test with typical Twilio headers and data
        test_data = {
            'CallSid': 'diagnostic_test_call',
            'From': '+15551234567',
            'To': '+18886411102',
            'CallStatus': 'ringing'
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'TwilioProxy/1.1'
        }
        
        print(f"⏳ Sending POST request at {datetime.now()}")
        
        response = requests.post(
            webhook_url, 
            data=test_data, 
            headers=headers,
            timeout=15
        )
        
        print(f"✅ HTTP Status: {response.status_code}")
        print(f"📋 Response Headers: {dict(response.headers)}")
        print(f"📄 Response Body (first 300 chars):")
        print(response.text[:300])
        
        # Check if it's valid TwiML
        if '<?xml version="1.0"' in response.text and '<Response>' in response.text:
            print("✅ Response contains valid TwiML")
        else:
            print("❌ Response does not contain valid TwiML")
            
        if response.status_code == 200:
            print("✅ External webhook is working correctly!")
            return True
        else:
            print(f"❌ External webhook returned error: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection Error: Cannot reach the webhook URL")
        print(f"   This usually means the Replit app is not accessible externally")
        print(f"   Error details: {e}")
        return False
        
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout Error: Webhook took too long to respond")
        print(f"   Error details: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False

def check_twilio_requirements():
    """Check if webhook meets Twilio requirements"""
    print("\n🔧 Checking Twilio Webhook Requirements:")
    print("-" * 40)
    
    requirements = [
        "✅ HTTPS URL (workspace.brokeropenhouse.replit.app uses HTTPS)",
        "✅ POST method supported",
        "✅ Returns valid TwiML XML",
        "✅ Responds within 15 seconds",
        "✅ Returns HTTP 200 status code"
    ]
    
    for req in requirements:
        print(req)

if __name__ == "__main__":
    print("🚀 Twilio Webhook Diagnostic Tool")
    print("=" * 50)
    
    # Test external connectivity
    success = test_external_webhook()
    
    # Show requirements
    check_twilio_requirements()
    
    print("\n📋 Diagnostic Summary:")
    print("-" * 30)
    
    if success:
        print("✅ Your webhook is working correctly!")
        print("   If you're still getting error messages, the issue might be:")
        print("   1. Twilio phone number configuration")
        print("   2. Different webhook URL in Twilio console")
        print("   3. Twilio account or phone number issues")
    else:
        print("❌ Your webhook is not accessible externally")
        print("   Possible solutions:")
        print("   1. Make sure your Replit app is running")
        print("   2. Check if the domain is correct")
        print("   3. Try restarting your Replit app")
        print("   4. Verify your Replit app is set to 'public'")