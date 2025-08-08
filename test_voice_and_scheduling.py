#!/usr/bin/env python3
"""
Test Chris's Voice Quality and Scheduling Knowledge
Check ElevenLabs integration and accurate day/scheduling information
"""

import requests
import json
import time
import urllib.parse
from datetime import datetime
import pytz

def test_voice_and_scheduling():
    """Test Chris's voice quality and scheduling accuracy"""
    
    base_url = "http://0.0.0.0:5000"
    
    # Get current day info
    eastern = pytz.timezone('US/Eastern')
    now_et = datetime.now(eastern)
    current_day = now_et.strftime('%A')
    
    print("🎙️ VOICE QUALITY & SCHEDULING ACCURACY TEST")
    print(f"Current day: {current_day}, {now_et.strftime('%B %d, %Y at %I:%M %p ET')}")
    print("=" * 70)
    
    # Test scenarios focused on scheduling and voice
    test_scenarios = [
        {
            "speech": "when can someone come fix my heating?",
            "call_sid": "VOICE_SCHEDULE_001",
            "expect": ["soon", "quickly", "priority", "right away"],
            "avoid": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "test_name": "Maintenance Scheduling - No False Promises"
        },
        {
            "speech": "what day is today?",
            "call_sid": "VOICE_SCHEDULE_002", 
            "expect": [current_day.lower()],
            "avoid": ["monday", "saturday"] if current_day not in ["Monday", "Saturday"] else ["sunday"],
            "test_name": "Current Day Knowledge"
        },
        {
            "speech": "can you send someone on Monday?",
            "call_sid": "VOICE_SCHEDULE_003",
            "expect": ["check", "see", "try", "possible"],
            "avoid": ["yes", "definitely", "sure", "absolutely"] if current_day == "Friday" else [],
            "test_name": "Scheduling Request Handling"
        },
        {
            "speech": "are you guys open today?",
            "call_sid": "VOICE_SCHEDULE_004",
            "expect": ["hours", "9", "5", "eastern"],
            "avoid": ["closed", "weekend"] if now_et.weekday() < 5 else [],
            "test_name": "Business Hours Inquiry"
        }
    ]
    
    all_passed = True
    voice_quality_notes = []
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n{i+1}. {scenario['test_name'].upper()}")
        print("-" * 60)
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
                    
                    # Check for voice quality indicators
                    if "'" in ai_response or "n't" in ai_response or "I'll" in ai_response:
                        voice_quality_notes.append("✅ Uses contractions (natural speech)")
                    
                    if len(ai_response.split()) < 15:
                        voice_quality_notes.append("✅ Concise response (not robotic)")
                    
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
                            print(f"   Made false promises: {avoided_found}")
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
        
        time.sleep(1)
    
    print("\n" + "=" * 70)
    print("🎯 VOICE & SCHEDULING TEST COMPLETE")
    
    # Voice quality summary
    if voice_quality_notes:
        print("\n🎙️ VOICE QUALITY NOTES:")
        for note in set(voice_quality_notes):  # Remove duplicates
            print(f"   {note}")
    
    if all_passed:
        print("✅ SUCCESS: Chris sounds natural and gives accurate scheduling info")
    else:
        print("⚠️ IMPROVEMENTS NEEDED: Voice or scheduling issues found")
        
    return all_passed

if __name__ == "__main__":
    success = test_voice_and_scheduling()
    if success:
        print("🎉 CHRIS IS READY WITH NATURAL VOICE AND ACCURATE SCHEDULING")
    else:
        print("🔧 CHRIS NEEDS VOICE/SCHEDULING IMPROVEMENTS")