#!/usr/bin/env python3
"""
Test Chris's Critical Fixes
- Memory (not asking for address twice)
- Collecting name, phone, unit
- No false promises about 24/7 or tonight service
- Correct business hours (closed after 5 PM)
- Better silent response
"""

import requests
import json
import time
import urllib.parse
from datetime import datetime
import pytz

def test_chris_fixes():
    """Test Chris's critical fixes for reported issues"""
    
    base_url = "http://0.0.0.0:5000"
    
    print("🔧 CHRIS CRITICAL FIXES TEST")
    print("Testing: Memory, Contact Info Collection, Business Hours, False Promises")
    print("=" * 70)
    
    # Test conversation memory and information collection
    test_scenarios = [
        {
            "speech": "I live at 31 Port Richmond Avenue",
            "call_sid": "MEMORY_TEST_001",
            "step": "Address given",
            "expect": ["got it", "address", "name", "what's your name"],
            "avoid": ["address again", "where", "what address"],
            "test_name": "Step 1: Address Memory Test"
        },
        {
            "speech": "My name is John Smith",
            "call_sid": "MEMORY_TEST_001", 
            "step": "Name given",
            "expect": ["john", "phone", "number", "contact"],
            "avoid": ["address", "where do you live"],
            "test_name": "Step 2: Name Collection + No Address Re-ask"
        },
        {
            "speech": "555-123-4567",
            "call_sid": "MEMORY_TEST_001",
            "step": "Phone given", 
            "expect": ["unit", "apartment", "problem", "issue"],
            "avoid": ["address", "name", "phone"],
            "test_name": "Step 3: Phone Collection + Ask for Unit/Issue"
        },
        {
            "speech": "can someone come fix my heat tonight?",
            "call_sid": "BUSINESS_HOURS_001",
            "step": "After hours request",
            "expect": ["closed", "monday", "morning", "business hours"],
            "avoid": ["tonight", "24/7", "emergency", "someone will be out"],
            "test_name": "Business Hours: No False Promises"
        },
        {
            "speech": "do you guys offer 24/7 service?",
            "call_sid": "SERVICE_HOURS_001", 
            "step": "24/7 inquiry",
            "expect": ["9 am", "5 pm", "monday", "friday", "closed"],
            "avoid": ["24/7", "emergency", "anytime", "always"],
            "test_name": "Service Hours: Accurate Information"
        }
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n{i+1}. {scenario['test_name'].upper()}")
        print("-" * 60)
        print(f"Step: {scenario['step']}")
        print(f"Testing: \"{scenario['speech']}\"")
        
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
                    
                    # Check avoided keywords (false promises)
                    avoided_found = []
                    for keyword in scenario.get('avoid', []):
                        if keyword.lower() in response_lower:
                            avoided_found.append(keyword)
                    
                    # Evaluate results
                    if expected_found and not avoided_found:
                        if expected_missing:
                            print(f"✅ MOSTLY PASSED: Found {expected_found}, Missing: {expected_missing}")
                        else:
                            print("✅ PASSED: All expectations met")
                    else:
                        print("❌ FAILED:")
                        if expected_missing:
                            print(f"   Missing expected: {expected_missing}")
                        if avoided_found:
                            print(f"   Found problematic responses: {avoided_found}")
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
        
        time.sleep(1.5)  # Pause between tests
    
    print("\n" + "=" * 70)
    print("🎯 CHRIS CRITICAL FIXES TEST COMPLETE")
    
    if all_passed:
        print("✅ SUCCESS: Chris remembers info, collects contact details, and gives accurate business info")
    else:
        print("⚠️ IMPROVEMENTS NEEDED: Some critical issues remain")
        
    return all_passed

if __name__ == "__main__":
    success = test_chris_fixes()
    if success:
        print("🎉 CHRIS IS READY WITH ALL CRITICAL FIXES")
    else:
        print("🔧 CHRIS NEEDS MORE IMPROVEMENTS")