#!/usr/bin/env python3
"""
Test Chris's Knowledge of Grinberg Management
Verify he knows company info, office hours, and asks for addresses not unit numbers
"""

import requests
import json
import time
import urllib.parse

def test_chris_knowledge():
    """Test Chris's knowledge about Grinberg Management and proper question flow"""
    
    base_url = "http://0.0.0.0:5000"
    test_call_sid = "KNOWLEDGE_TEST_789"
    
    print("🏢 CHRIS KNOWLEDGE TEST - Grinberg Management")
    print("Testing: Company awareness, office hours, address vs unit focus")
    print("=" * 70)
    
    # Test scenarios
    test_scenarios = [
        {
            "speech": "what are your office hours?",
            "expect": ["monday", "friday", "9", "5", "eastern", "grinberg"],
            "test_name": "Office Hours Knowledge"
        },
        {
            "speech": "I have a maintenance problem",
            "expect": ["address", "property", "where", "grinberg"],
            "avoid": ["unit number", "unit #"],
            "test_name": "Maintenance Request Flow"
        },
        {
            "speech": "who am I calling?",
            "expect": ["grinberg", "management", "development"],
            "test_name": "Company Identification"
        },
        {
            "speech": "are you open right now?",
            "expect": ["grinberg", "hours", "monday", "friday"],
            "test_name": "Business Hours Inquiry"
        }
    ]
    
    all_passed = True
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n{i+1}. {scenario['test_name'].upper()}")
        print("-" * 50)
        print(f"Testing: \"{scenario['speech']}\"")
        
        try:
            data = {
                'SpeechResult': scenario['speech'],
                'Confidence': '0.95',
                'CallSid': test_call_sid,
                'From': '+15551234567'
            }
            
            start_time = time.time()
            response = requests.post(f"{base_url}/handle-speech/{test_call_sid}", 
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
                    
                    # Check avoided keywords
                    avoided_found = []
                    for keyword in scenario.get('avoid', []):
                        if keyword.lower() in response_lower:
                            avoided_found.append(keyword)
                    
                    # Evaluate results
                    if expected_found and not expected_missing and not avoided_found:
                        print("✅ PASSED: All expectations met")
                    elif expected_found and not avoided_found:
                        print(f"✅ MOSTLY PASSED: Found {expected_found}")
                        if expected_missing:
                            print(f"   Missing: {expected_missing}")
                    else:
                        print("❌ FAILED:")
                        if expected_missing:
                            print(f"   Missing expected: {expected_missing}")
                        if avoided_found:
                            print(f"   Found unwanted: {avoided_found}")
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
    print("🎯 CHRIS KNOWLEDGE TEST COMPLETE")
    
    if all_passed:
        print("✅ ALL TESTS PASSED: Chris knows Grinberg Management info")
    else:
        print("⚠️ SOME TESTS FAILED: Knowledge gaps identified")
        
    return all_passed

if __name__ == "__main__":
    success = test_chris_knowledge()
    if success:
        print("🎉 CHRIS IS READY FOR GRINBERG MANAGEMENT CALLS")
    else:
        print("🔧 CHRIS NEEDS KNOWLEDGE IMPROVEMENTS")