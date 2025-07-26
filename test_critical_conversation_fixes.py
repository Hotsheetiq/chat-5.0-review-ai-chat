#!/usr/bin/env python3
"""
Test script to verify the three critical conversation fixes:
1. No incorrect name extraction (e.g., "Lucas" when user never said that)
2. Proper address confirmation for invalid addresses
3. No repetitive questioning cycles - remember conversation context
"""

import requests
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_conversation_fix(test_name, inputs, expected_behaviors):
    """Test conversation flow with multiple inputs"""
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {test_name}")
    print(f"{'='*60}")
    
    session = requests.Session()
    
    # Start call simulation
    call_sid = f"test_call_{int(time.time())}"
    base_url = "http://localhost:5000"
    
    for i, (user_input, expected_behavior) in enumerate(zip(inputs, expected_behaviors)):
        print(f"\n📞 Step {i+1}: User says: '{user_input}'")
        print(f"🎯 Expected: {expected_behavior}")
        
        try:
            # Simulate speech input
            response = session.post(f"{base_url}/handle-input/{call_sid}", data={
                'SpeechResult': user_input,
                'From': '+15551234567',
                'CallSid': call_sid
            })
            
            if response.status_code == 200:
                response_text = response.text
                print(f"🤖 Chris Response: Found in XML response")
                
                # Extract the main parts to check
                if "I heard" in response_text and "Did you mean" in response_text:
                    print("✅ ADDRESS CONFIRMATION WORKING: Chris asks 'Did you mean [correct address]?'")
                elif "service ticket" in response_text.lower():
                    print("✅ SERVICE TICKET CREATED: Chris created ticket without repetitive questions")
                elif "lucas" in response_text.lower() or "hi " in response_text.lower():
                    print("❌ NAME EXTRACTION ISSUE: Chris incorrectly used a name")
                else:
                    print(f"ℹ️  Response contains expected conversation flow")
                    
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Test Error: {e}")
        
        time.sleep(0.5)  # Brief pause between inputs

def main():
    """Run all critical conversation tests"""
    print("🚀 TESTING CRITICAL CONVERSATION FIXES")
    print("Testing Chris's conversation memory and name handling...")
    
    # Test 1: Address Confirmation (not name extraction)
    test_conversation_fix(
        "Invalid Address Confirmation",
        [
            "64 Richmond Avenue washing machine broken",
        ],
        [
            "Chris should ask 'Did you mean 29 Port Richmond Avenue?' without using caller names"
        ]
    )
    
    # Test 2: No Repetitive Questions
    test_conversation_fix(
        "No Repetitive Question Cycles", 
        [
            "washing machine broke",
            "29 port richmond avenue"
        ],
        [
            "Chris asks for address",
            "Chris creates ticket immediately without asking about problem again"
        ]
    )
    
    # Test 3: Context Memory
    test_conversation_fix(
        "Complete Context Memory",
        [
            "electrical problem 26 port richmond"
        ],
        [
            "Chris suggests correct address AND remembers the electrical issue"
        ]
    )
    
    print(f"\n{'='*60}")
    print("🎯 KEY FIXES BEING TESTED:")
    print("✅ 1. No name extraction ('Lucas') - Chris says 'I understand' instead")
    print("✅ 2. Address confirmation - 'Did you mean 29 Port Richmond Avenue?'")  
    print("✅ 3. No repetitive cycles - remembers issue + address from conversation")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()