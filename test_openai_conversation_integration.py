#!/usr/bin/env python3
"""
Test the new OpenAI Conversation Manager Integration
Simulates a call to verify the three-mode system is working
"""

import requests
import urllib.parse
import json
import time

def test_conversation_manager():
    """Test the conversation manager with simulated speech input"""
    
    base_url = "http://0.0.0.0:5000"
    test_call_sid = "TEST_CALL_12345"
    
    print("🧪 Testing OpenAI Conversation Manager Integration")
    print("=" * 60)
    
    # Test 1: Simple maintenance request (should use default mode)
    test_speech = "hi, i'm having problem with my stove"
    
    print(f"Test 1: Default Mode - '{test_speech}'")
    
    try:
        # Simulate Twilio speech webhook
        data = {
            'SpeechResult': test_speech,
            'Confidence': '0.95',
            'CallSid': test_call_sid,
            'From': '+15551234567'
        }
        
        start_time = time.time()
        response = requests.post(f"{base_url}/handle-speech/{test_call_sid}", data=data, timeout=30)
        response_time = time.time() - start_time
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Time: {response_time:.3f}s")
        
        if response.status_code == 200:
            # Parse TwiML response
            response_text = response.text
            if '<Play>' in response_text:
                play_url = response_text.split('<Play>')[1].split('</Play>')[0]
                # Extract text from URL
                if 'text=' in play_url:
                    encoded_text = play_url.split('text=')[1].split('&')[0].split('"')[0]
                    ai_response = urllib.parse.unquote(encoded_text)
                    print(f"AI Response: {ai_response}")
                    print("✅ Default mode test passed")
                else:
                    print("❌ No text found in response")
            else:
                print("❌ No Play element found in TwiML")
                print(f"Raw response: {response_text[:200]}...")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
    
    print("\n" + "=" * 60)
    
    # Test 2: Check voice mode switching
    print("Test 2: Voice Mode Switching")
    
    try:
        # Switch to live mode
        response = requests.post(f"{base_url}/voice-mode/live", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Successfully switched to live mode: {data.get('message')}")
            else:
                print(f"❌ Mode switch failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error switching mode: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Mode switching test failed: {e}")
    
    # Test 3: Check voice status
    try:
        response = requests.get(f"{base_url}/voice-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                status = data.get('openai_status', {})
                print(f"✅ Current mode: {status.get('current_mode')}")
                print(f"✅ Available modes: {status.get('available_modes')}")
            else:
                print(f"❌ Status check failed: {data.get('error')}")
        else:
            print(f"❌ HTTP Error checking status: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Status check test failed: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 OpenAI Conversation Manager Integration Test Complete")

if __name__ == "__main__":
    test_conversation_manager()