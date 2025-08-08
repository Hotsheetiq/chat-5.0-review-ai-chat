#!/usr/bin/env python3
"""
Test Chris's Plain Language and Greeting Behavior
Verify he uses simple words, time-based greetings, and doesn't repeat introductions
"""

import requests
import json
import time
import urllib.parse
from datetime import datetime
import pytz

def test_plain_language_chris():
    """Test Chris's plain language and greeting behavior"""
    
    base_url = "http://0.0.0.0:5000"
    
    # Get current time for greeting test
    eastern = pytz.timezone('US/Eastern')
    now_et = datetime.now(eastern)
    hour = now_et.hour
    
    if 6 <= hour < 12:
        expected_greeting = "good morning"
    elif 12 <= hour < 18:
        expected_greeting = "good afternoon"
    else:
        expected_greeting = "good evening"
    
    print("🗣️ CHRIS PLAIN LANGUAGE & GREETING TEST")
    print(f"Current time: {now_et.strftime('%I:%M %p ET')} - Expecting: {expected_greeting}")
    print("=" * 70)
    
    # Test scenarios
    test_scenarios = [
        {
            "speech": "hello",
            "call_sid": "GREETING_TEST_001",
            "expect_greeting": True,
            "expect": [expected_greeting, "chris", "grinberg"],
            "avoid": ["assistance", "experiencing", "comprehensive", "facilitate"],
            "test_name": "First Call - Time-Based Greeting"
        },
        {
            "speech": "I have a heating problem at my apartment",
            "call_sid": "GREETING_TEST_001",  # Same call
            "expect_greeting": False,
            "expect": ["address", "where", "heat"],
            "avoid": ["this is chris", "grinberg management", "assistance", "experiencing"],
            "test_name": "Follow-Up - No Re-Introduction"
        },
        {
            "speech": "can you help me with an issue?",
            "call_sid": "PLAIN_TEST_002",
            "expect_greeting": True,
            "expect": [expected_greeting, "help", "what", "problem"],
            "avoid": ["assistance", "experiencing", "facilitate", "comprehensive"],
            "test_name": "New Call - Plain Language Response"
        },
        {
            "speech": "my stove isn't working properly",
            "call_sid": "PLAIN_TEST_002",  # Same call
            "expect_greeting": False, 
            "expect": ["address", "where", "stove"],
            "avoid": ["this is chris", "assistance", "experiencing", "malfunction"],
            "test_name": "Same Call - Simple Language"
        }
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n{i+1}. {scenario['test_name'].upper()}")
        print("-" * 60)
        print(f"Testing: \"{scenario['speech']}\"")
        print(f"Call ID: {scenario['call_sid']} (Expect greeting: {scenario['expect_greeting']})")
        
        try:
            data = {
                'SpeechResult': scenario['speech'],
                'Confidence': '0.95',
                'CallSid': scenario['call_sid'],
                'From': '+15551234567'
            }
            
            start_time = time.time()
            response = requests.post(f"{base_url}/handle-speech/{scenario['call_sid']}", 
                                   data=data, timeout=20)
            response_time = time.time() - start_time
            
            if response.status_code == 200 and '<Play>' in response.text:
                # Extract AI response
                play_url = response.text.split('<Play>')[1].split('</Play>')[0]
                if 'text=' in play_url:
                    encoded_text = play_url.split('text=')[1].split('&')[0].split('"')[0]
                    ai_response = urllib.parse.unquote(encoded_text)
                    
                    print(f"Chris ({response_time:.3f}s): {ai_response}")
                    
                    # Check expected keywords
                    response_lower = ai_response.lower()
                    expected_found = []
                    expected_missing = []
                    
                    for keyword in scenario.get('expect', []):
                        if keyword.lower() in response_lower:
                            expected_found.append(keyword)
                        else:
                            expected_missing.append(keyword)
                    
                    # Check avoided keywords (fancy words)
                    avoided_found = []
                    for keyword in scenario.get('avoid', []):
                        if keyword.lower() in response_lower:
                            avoided_found.append(keyword)
                    
                    # Check greeting behavior
                    greeting_correct = True
                    if scenario['expect_greeting']:
                        if not any(word in response_lower for word in ['good morning', 'good afternoon', 'good evening']):
                            greeting_correct = False
                            print("❌ Missing expected time-based greeting")
                    else:
                        if any(word in response_lower for word in ['this is chris', 'chris from grinberg']):
                            greeting_correct = False
                            print("❌ Unexpected re-introduction (should only greet once per call)")
                    
                    # Evaluate results
                    if expected_found and not avoided_found and greeting_correct:
                        if expected_missing:
                            print(f"✅ MOSTLY PASSED: Found {expected_found}, Missing: {expected_missing}")
                        else:
                            print("✅ PASSED: All expectations met")
                    else:
                        print("❌ FAILED:")
                        if expected_missing:
                            print(f"   Missing expected: {expected_missing}")
                        if avoided_found:
                            print(f"   Found fancy words: {avoided_found}")
                        if not greeting_correct:
                            print("   Greeting behavior incorrect")
                        all_passed = False
                    
                else:
                    print("❌ No response text found")
                    all_passed = False
            else:
                print(f"❌ Request failed: {response.status_code}")
                all_passed = False
                
        except Exception as e:
            print(f"❌ Error: {e}")
            all_passed = False
        
        time.sleep(1)  # Brief pause between tests
    
    print("\n" + "=" * 70)
    print("🎯 PLAIN LANGUAGE & GREETING TEST COMPLETE")
    
    if all_passed:
        print("✅ SUCCESS: Chris uses plain language and proper greeting behavior")
    else:
        print("⚠️ IMPROVEMENTS NEEDED: Some language or greeting issues found")
        
    return all_passed

if __name__ == "__main__":
    success = test_plain_language_chris()
    if success:
        print("🎉 CHRIS IS READY WITH PLAIN LANGUAGE AND PROPER GREETINGS")
    else:
        print("🔧 CHRIS NEEDS LANGUAGE/GREETING IMPROVEMENTS")