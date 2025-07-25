#!/usr/bin/env python3
import requests

def debug_application_error():
    """Debug the application error by testing webhook responses"""
    
    # Correct webhook URL
    correct_url = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/voice"
    
    # Wrong URLs that might be configured in Twilio
    wrong_urls = [
        "https://workspace-brokeropenhouse.replit.app/voice",
        "https://workspace.brokeropenhouse.replit.app/voice"
    ]
    
    print("=== DEBUGGING APPLICATION ERROR ===")
    
    # Test correct URL
    print(f"\n1. Testing CORRECT URL: {correct_url}")
    try:
        response = requests.post(correct_url, 
                               data={'CallSid': 'debug_test', 'From': '+15551234567'}, 
                               timeout=5, verify=False)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ WORKING - Returns valid TwiML")
            print(f"   ElevenLabs: {'<Play>' in response.text}")
        else:
            print(f"   ❌ ERROR: {response.text[:100]}")
    except Exception as e:
        print(f"   ❌ CONNECTION ERROR: {e}")
    
    # Test wrong URLs
    for i, wrong_url in enumerate(wrong_urls, 2):
        print(f"\n{i}. Testing WRONG URL: {wrong_url}")
        try:
            response = requests.post(wrong_url, 
                                   data={'CallSid': 'debug_test', 'From': '+15551234567'}, 
                                   timeout=5, verify=False)
            print(f"   Status: {response.status_code}")
            if response.status_code == 404:
                print("   ❌ NOT FOUND - This causes Twilio application errors!")
            else:
                print(f"   Response: {response.text[:100]}")
        except Exception as e:
            print(f"   ❌ CONNECTION ERROR: {e}")
    
    print("\n=== SOLUTION ===")
    print("If you're getting 'application error', your Twilio webhook URL is wrong.")
    print("Update Twilio console to use:")
    print(f"   {correct_url}")
    print("\nSteps:")
    print("1. Go to console.twilio.com")
    print("2. Phone Numbers → Manage → Active Numbers") 
    print("3. Click (888) 641-1102")
    print("4. Update webhook URL")
    print("5. Save configuration")

if __name__ == "__main__":
    debug_application_error()