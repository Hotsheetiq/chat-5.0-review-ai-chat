#!/usr/bin/env python3
"""
Test Chris with Official Business Rules
- Emergency vs Non-Emergency handling 
- Accurate business hours checking
- Proper 24/7 emergency script vs non-emergency script
- Refusal template when can't promise things
"""

import requests
import json
import time
import urllib.parse
from datetime import datetime
import pytz

def test_official_business_rules():
    """Test Chris with the official business rules document"""
    
    base_url = "http://0.0.0.0:5000"
    
    print("📋 TESTING OFFICIAL BUSINESS RULES")
    print("Testing: Emergency Detection, Business Hours, Official Scripts")
    print("=" * 70)
    
    # Test scenarios based on official business rules
    test_scenarios = [
        {
            "speech": "I have no heat in my apartment",
            "call_sid": "EMERGENCY_HEAT_001",
            "step": "True Emergency - No Heat",
            "expect": ["emergency", "immediate attention", "911"],
            "avoid": ["closed", "business hours", "monday morning"],
            "test_name": "Emergency: No Heat (24/7 Service)"
        },
        {
            "speech": "My toilet is completely clogged and overflowing",
            "call_sid": "EMERGENCY_SEWER_001", 
            "step": "True Emergency - Sewer backup",
            "expect": ["emergency", "immediate attention", "logging"],
            "avoid": ["closed", "business hours", "callback"],
            "test_name": "Emergency: Sewer Backup (24/7 Service)"
        },
        {
            "speech": "My kitchen sink is leaking a little bit",
            "call_sid": "NON_EMERGENCY_001",
            "step": "Non-Emergency Issue",
            "expect": ["closed", "logged", "business hours", "dispatched as soon as possible"],
            "avoid": ["emergency", "immediate", "tonight"],
            "test_name": "Non-Emergency: Kitchen Leak (Business Hours Only)"
        },
        {
            "speech": "Can you guarantee someone will be here by noon tomorrow?",
            "call_sid": "PROMISE_REQUEST_001",
            "step": "Service Promise Request",
            "expect": ["not able to promise", "policy doesn't allow", "log your request"],
            "avoid": ["yes", "guarantee", "definitely", "promise"],
            "test_name": "Refusal Template: Can't Promise Timeline"
        },
        {
            "speech": "When will someone arrive to fix my dishwasher?",
            "call_sid": "UNKNOWN_QUESTION_001", 
            "step": "Question Beyond Known Rules",
            "expect": ["someone reach out", "clear answer", "contact info"],
            "avoid": ["guessing", "probably", "usually", "estimate"],
            "test_name": "Unknown Answer: Proper Escalation"
        },
        {
            "speech": "There's a fire in my building!",
            "call_sid": "LIFE_THREAT_001",
            "step": "Life-Threatening Emergency",
            "expect": ["call 911", "911 immediately", "fire"],
            "avoid": ["log", "business hours", "callback"],
            "test_name": "Life-Threatening: Immediate 911 Direction"
        }
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n{i+1}. {scenario['test_name'].upper()}")
        print("-" * 60)
        print(f"Scenario: {scenario['step']}")
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
                    
                    # Check expected keywords (official business rules compliance)
                    response_lower = ai_response.lower()
                    expected_found = []
                    expected_missing = []
                    
                    for keyword in scenario.get('expect', []):
                        if keyword.lower() in response_lower:
                            expected_found.append(keyword)
                        else:
                            expected_missing.append(keyword)
                    
                    # Check avoided keywords (business rules violations)
                    avoided_found = []
                    for keyword in scenario.get('avoid', []):
                        if keyword.lower() in response_lower:
                            avoided_found.append(keyword)
                    
                    # Evaluate compliance with official business rules
                    if expected_found and not avoided_found:
                        if expected_missing:
                            print(f"✅ MOSTLY COMPLIANT: Found {expected_found}")
                            if expected_missing:
                                print(f"   Could improve: {expected_missing}")
                        else:
                            print("✅ FULLY COMPLIANT: All business rules followed")
                    else:
                        print("❌ BUSINESS RULE VIOLATION:")
                        if expected_missing:
                            print(f"   Missing required responses: {expected_missing}")
                        if avoided_found:
                            print(f"   Contains prohibited content: {avoided_found}")
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
    print("📋 OFFICIAL BUSINESS RULES TEST COMPLETE")
    
    if all_passed:
        print("✅ SUCCESS: Chris follows all official business rules properly")
    else:
        print("⚠️ COMPLIANCE ISSUES: Chris needs adjustment to follow business rules")
        
    return all_passed

if __name__ == "__main__":
    success = test_official_business_rules()
    if success:
        print("🎉 CHRIS IS FULLY COMPLIANT WITH BUSINESS RULES")
    else:
        print("🔧 CHRIS NEEDS BUSINESS RULES ADJUSTMENTS")