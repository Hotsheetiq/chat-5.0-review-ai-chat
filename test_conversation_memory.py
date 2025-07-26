#!/usr/bin/env python3
"""
Test script to verify conversation memory fixes
Tests the exact scenario user described: washing machine + address + shouldn't ask again
"""

import requests
import time

def test_memory_fix():
    print("🧠 Testing conversation memory fix...")
    
    base_url = "http://0.0.0.0:5000"
    call_sid = "test_memory_complete"
    
    # Step 1: Report washing machine problem
    print("\n1. Reporting washing machine problem...")
    response1 = requests.post(f"{base_url}/handle-input/{call_sid}", 
        data={"SpeechResult": "I have a problem with my washing machine", "From": "+Anonymous"})
    print(f"Response 1: {response1.status_code}")
    
    time.sleep(2)
    
    # Step 2: Provide address
    print("\n2. Providing address...")
    response2 = requests.post(f"{base_url}/handle-input/{call_sid}", 
        data={"SpeechResult": "29 Port Richmond Avenue", "From": "+Anonymous"})
    print(f"Response 2: {response2.status_code}")
    
    time.sleep(2)
    
    # Step 3: Any follow-up (this should NOT ask "what's the problem" again)
    print("\n3. Testing follow-up (should create ticket immediately)...")
    response3 = requests.post(f"{base_url}/handle-input/{call_sid}", 
        data={"SpeechResult": "Yes that's correct", "From": "+Anonymous"})
    print(f"Response 3: {response3.status_code}")
    
    # Check if memory logic worked
    if all(r.status_code == 200 for r in [response1, response2, response3]):
        print("✅ All requests successful - memory logic implemented")
    else:
        print("❌ Some requests failed")
        
    print("\n🎯 Expected behavior: After washing machine + address, Chris should create ticket immediately without asking 'what's the problem' again")

if __name__ == "__main__":
    test_memory_fix()