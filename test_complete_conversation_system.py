#!/usr/bin/env python3
"""
Complete Conversation System Test
Tests all three OpenAI modes and memory management
"""

import requests
import json
import time
import urllib.parse

def test_complete_system():
    """Test the complete conversation system with all three modes"""
    
    base_url = "http://0.0.0.0:5000"
    test_call_sid = "COMPLETE_TEST_67890"
    
    print("🎯 COMPLETE OPENAI THREE-MODE CONVERSATION SYSTEM TEST")
    print("=" * 70)
    
    # Test 1: Check system status
    print("1. SYSTEM STATUS CHECK")
    try:
        response = requests.get(f"{base_url}/voice-status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            if status.get('success', False):
                openai_status = status.get('openai_status', {})
                print(f"✅ Current Mode: {openai_status.get('current_mode')}")
                print(f"✅ Available Modes: {openai_status.get('available_modes')}")
                print(f"✅ System Status: {openai_status.get('system_status', 'unknown')}")
            else:
                print(f"❌ Status check failed: {status}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"❌ System check failed: {e}")
    
    print("\n" + "-" * 50)
    
    # Test 2: Default Mode - Simple maintenance request
    print("2. DEFAULT MODE TEST (Simple Request)")
    
    test_conversations = [
        "hi, my stove isn't working properly",
        "it's not heating up when I turn it on",
        "okay, please create a service request"
    ]
    
    for i, speech in enumerate(test_conversations):
        print(f"   User: {speech}")
        
        try:
            data = {
                'SpeechResult': speech,
                'Confidence': '0.95',
                'CallSid': test_call_sid,
                'From': '+15551234567'
            }
            
            start_time = time.time()
            response = requests.post(f"{base_url}/handle-speech/{test_call_sid}", data=data, timeout=20)
            response_time = time.time() - start_time
            
            if response.status_code == 200 and '<Play>' in response.text:
                play_url = response.text.split('<Play>')[1].split('</Play>')[0]
                if 'text=' in play_url:
                    encoded_text = play_url.split('text=')[1].split('&')[0].split('"')[0]
                    ai_response = urllib.parse.unquote(encoded_text)
                    print(f"   Chris: {ai_response} ({response_time:.3f}s)")
                    
                    # Check for intelligent response (not generic greeting)
                    if "help you today" not in ai_response.lower():
                        print("   ✅ Intelligent contextual response")
                    else:
                        print("   ⚠️ Generic response detected")
                else:
                    print(f"   ❌ No response text found")
            else:
                print(f"   ❌ Request failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(1)  # Brief pause between messages
    
    print("\n" + "-" * 50)
    
    # Test 3: Reasoning Mode - Complex query
    print("3. REASONING MODE TEST (Complex Analysis)")
    
    # Switch to reasoning mode first
    try:
        requests.post(f"{base_url}/voice-mode/reasoning", timeout=10)
        print("   Switched to reasoning mode")
    except:
        print("   ❌ Failed to switch to reasoning mode")
    
    complex_query = "I need a detailed analysis of converting my basement into a rental unit. What are the legal requirements, zoning considerations, and financial feasibility for Staten Island properties?"
    
    print(f"   User: {complex_query[:60]}...")
    
    try:
        data = {
            'SpeechResult': complex_query,
            'Confidence': '0.98',
            'CallSid': f"{test_call_sid}_REASONING",
            'From': '+15551234567'
        }
        
        start_time = time.time()
        response = requests.post(f"{base_url}/handle-speech/{test_call_sid}_REASONING", data=data, timeout=30)
        response_time = time.time() - start_time
        
        if response.status_code == 200 and '<Play>' in response.text:
            play_url = response.text.split('<Play>')[1].split('</Play>')[0]
            if 'text=' in play_url:
                encoded_text = play_url.split('text=')[1].split('&')[0].split('"')[0]
                ai_response = urllib.parse.unquote(encoded_text)
                print(f"   Chris: {ai_response[:100]}... ({response_time:.3f}s)")
                
                # Check for detailed response
                reasoning_indicators = ["analysis", "requirements", "zoning", "legal", "consider"]
                if any(indicator in ai_response.lower() for indicator in reasoning_indicators):
                    print("   ✅ Detailed reasoning response detected")
                else:
                    print("   ⚠️ Response may be too generic for reasoning mode")
            else:
                print("   ❌ No response text found")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Reasoning test error: {e}")
    
    print("\n" + "-" * 50)
    
    # Test 4: Live Mode - Quick interaction
    print("4. LIVE MODE TEST (Quick Response)")
    
    # Switch to live mode
    try:
        requests.post(f"{base_url}/voice-mode/live", timeout=10)
        print("   Switched to live mode")
    except:
        print("   ❌ Failed to switch to live mode")
    
    quick_query = "what's your phone number?"
    print(f"   User: {quick_query}")
    
    try:
        data = {
            'SpeechResult': quick_query,
            'Confidence': '0.99',
            'CallSid': f"{test_call_sid}_LIVE",
            'From': '+15551234567'
        }
        
        start_time = time.time()
        response = requests.post(f"{base_url}/handle-speech/{test_call_sid}_LIVE", data=data, timeout=15)
        response_time = time.time() - start_time
        
        if response.status_code == 200 and '<Play>' in response.text:
            play_url = response.text.split('<Play>')[1].split('</Play>')[0]
            if 'text=' in play_url:
                encoded_text = play_url.split('text=')[1].split('&')[0].split('"')[0]
                ai_response = urllib.parse.unquote(encoded_text)
                print(f"   Chris: {ai_response} ({response_time:.3f}s)")
                
                # Check for quick response
                if response_time < 2.0:
                    print("   ✅ Fast response time for live mode")
                else:
                    print(f"   ⚠️ Response time slower than expected: {response_time:.3f}s")
            else:
                print("   ❌ No response text found")
        else:
            print(f"   ❌ Request failed: {response.status_code}")
    
    except Exception as e:
        print(f"   ❌ Live mode test error: {e}")
    
    print("\n" + "=" * 70)
    
    # Final status check
    print("5. FINAL SYSTEM STATUS")
    try:
        response = requests.get(f"{base_url}/voice-status", timeout=10)
        if response.status_code == 200:
            status = response.json()
            if status.get('success', False):
                print("✅ OpenAI Three-Mode Conversation System: OPERATIONAL")
                openai_status = status.get('openai_status', {})
                print(f"   Current Mode: {openai_status.get('current_mode')}")
                print(f"   System Ready: {openai_status.get('system_status', 'unknown')}")
            else:
                print("❌ System status check failed")
        else:
            print("❌ Unable to verify final status")
    except Exception as e:
        print(f"❌ Final status check error: {e}")
    
    print("\n🎯 COMPREHENSIVE CONVERSATION SYSTEM TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    test_complete_system()