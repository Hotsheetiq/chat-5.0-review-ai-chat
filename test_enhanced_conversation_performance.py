#!/usr/bin/env python3
"""
Test Enhanced Conversation Performance
Tests the improved memory management and fast response times
"""

import requests
import json
import time
import urllib.parse

def test_enhanced_performance():
    """Test the enhanced conversation system with session facts and fast responses"""
    
    base_url = "http://0.0.0.0:5000"
    test_call_sid = "ENHANCED_TEST_456"
    
    print("🚀 ENHANCED CONVERSATION PERFORMANCE TEST")
    print("Testing: Session Facts, Memory Retention, Fast Responses")
    print("=" * 70)
    
    # Test conversation flow with memory retention
    test_flow = [
        {
            "speech": "hi, I'm having a problem with my stove",
            "expect_facts": {"issue": "stove"},
            "expect_memory": "first_interaction"
        },
        {
            "speech": "I'm in unit 205A",
            "expect_facts": {"unit": "205A"},
            "expect_memory": "unit_provided"
        },
        {
            "speech": "it won't heat up when I turn it on",
            "expect_facts": {},
            "expect_memory": "issue_details"
        },
        {
            "speech": "can you create a service request?",
            "expect_facts": {},
            "expect_memory": "service_request"
        }
    ]
    
    total_response_time = 0
    conversation_count = 0
    
    print("1. CONVERSATION FLOW WITH MEMORY TEST")
    print("-" * 50)
    
    for i, turn in enumerate(test_flow):
        print(f"\nTurn {i+1}: {turn['speech']}")
        
        try:
            data = {
                'SpeechResult': turn['speech'],
                'Confidence': '0.95',
                'CallSid': test_call_sid,
                'From': '+15551234567'
            }
            
            start_time = time.time()
            response = requests.post(f"{base_url}/handle-speech/{test_call_sid}", 
                                   data=data, timeout=20)
            response_time = time.time() - start_time
            total_response_time += response_time
            conversation_count += 1
            
            if response.status_code == 200 and '<Play>' in response.text:
                # Extract AI response
                play_url = response.text.split('<Play>')[1].split('</Play>')[0]
                if 'text=' in play_url:
                    encoded_text = play_url.split('text=')[1].split('&')[0].split('"')[0]
                    ai_response = urllib.parse.unquote(encoded_text)
                    
                    print(f"Chris ({response_time:.3f}s): {ai_response}")
                    
                    # Check response quality
                    if response_time < 1.0:
                        print("✅ Fast response (< 1 second)")
                    else:
                        print(f"⚠️ Slow response ({response_time:.3f}s)")
                    
                    # Check for memory retention (no repeated questions)
                    lower_response = ai_response.lower()
                    
                    # Check if system is asking for already provided information
                    if i >= 1 and "unit" in lower_response and "number" in lower_response:
                        print("❌ Asking for unit number again - memory failure")
                    elif i >= 0 and "problem" in lower_response and "issue" in lower_response and i > 2:
                        print("❌ Asking for problem again - memory failure")
                    else:
                        print("✅ No repeated questions detected")
                    
                    # Check for contextual understanding
                    if i == 3 and any(word in lower_response for word in ['request', 'service', 'maintenance']):
                        print("✅ Understands service request context")
                    
                else:
                    print("❌ No response text found")
            else:
                print(f"❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(0.5)  # Brief pause between turns
    
    # Calculate average response time
    avg_response_time = total_response_time / conversation_count if conversation_count > 0 else 0
    
    print("\n" + "=" * 70)
    print("2. PERFORMANCE SUMMARY")
    print(f"Average Response Time: {avg_response_time:.3f}s")
    print(f"Total Turns: {conversation_count}")
    
    if avg_response_time < 1.0:
        print("✅ PERFORMANCE TARGET MET: Average < 1 second")
    else:
        print(f"❌ PERFORMANCE BELOW TARGET: {avg_response_time:.3f}s > 1.0s")
    
    # Test 3: Memory persistence across mode switches
    print("\n3. MEMORY PERSISTENCE TEST")
    print("-" * 50)
    
    try:
        # Switch to live mode
        mode_response = requests.post(f"{base_url}/voice-mode/live", timeout=10)
        if mode_response.status_code == 200:
            print("✅ Switched to live mode")
            
            # Continue conversation in live mode
            data = {
                'SpeechResult': 'what was my unit number again?',
                'Confidence': '0.95',
                'CallSid': test_call_sid,
                'From': '+15551234567'
            }
            
            start_time = time.time()
            response = requests.post(f"{base_url}/handle-speech/{test_call_sid}", 
                                   data=data, timeout=15)
            response_time = time.time() - start_time
            
            if response.status_code == 200 and '<Play>' in response.text:
                play_url = response.text.split('<Play>')[1].split('</Play>')[0]
                if 'text=' in play_url:
                    encoded_text = play_url.split('text=')[1].split('&')[0].split('"')[0]
                    ai_response = urllib.parse.unquote(encoded_text)
                    
                    print(f"Chris (live mode, {response_time:.3f}s): {ai_response}")
                    
                    if "205a" in ai_response.lower() or "205" in ai_response.lower():
                        print("✅ Memory persisted across mode switch")
                    else:
                        print("❌ Memory lost during mode switch")
                else:
                    print("❌ No response in live mode test")
            else:
                print(f"❌ Live mode test failed: {response.status_code}")
        else:
            print("❌ Failed to switch to live mode")
            
    except Exception as e:
        print(f"❌ Memory persistence test error: {e}")
    
    print("\n" + "=" * 70)
    print("🎯 ENHANCED CONVERSATION PERFORMANCE TEST COMPLETE")
    
    return avg_response_time < 1.0

if __name__ == "__main__":
    success = test_enhanced_performance()
    if success:
        print("🎉 ALL PERFORMANCE TARGETS MET")
    else:
        print("⚠️ PERFORMANCE IMPROVEMENTS NEEDED")