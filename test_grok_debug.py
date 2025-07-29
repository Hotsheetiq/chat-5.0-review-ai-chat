#!/usr/bin/env python3
"""
🧪 4. CONTROLLED TEST - Debug Grok API Response Parsing
Test both Grok 4.0 and 2.0 with static prompts to identify parsing issues
"""

import os
import json
import logging
from grok_integration import GrokAI

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_grok_models():
    """Run controlled tests with static prompts on both Grok models"""
    print("=" * 60)
    print("🧪 CONTROLLED GROK DEBUG TEST")
    print("=" * 60)
    
    try:
        # Initialize Grok AI
        grok_ai = GrokAI()
        
        # Test cases with progressively complex prompts
        test_cases = [
            {
                "name": "Simple Hello Test",
                "messages": [{"role": "user", "content": "Say hello"}]
            },
            {
                "name": "Complaint Confirmation Test", 
                "messages": [
                    {
                        "role": "system",
                        "content": "You are Chris from Grinberg Management. When tenant expresses any complaint, repeat it back to confirm understanding."
                    },
                    {
                        "role": "user", 
                        "content": "I have roaches in my apartment"
                    }
                ]
            },
            {
                "name": "Maintenance Issue Test",
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are Chris, a property management assistant. Help with maintenance issues."
                    },
                    {
                        "role": "user",
                        "content": "My heating is not working"
                    }
                ]
            }
        ]
        
        # Test each case
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🔬 TEST {i}: {test_case['name']}")
            print("-" * 40)
            
            try:
                response = grok_ai.generate_response(
                    messages=test_case["messages"],
                    max_tokens=150,
                    temperature=0.7,
                    timeout=5.0
                )
                
                print(f"✅ SUCCESS: Response received")
                print(f"📝 Response: {repr(response)}")
                print(f"📏 Length: {len(response)}")
                
                # Validate response quality
                if len(response.strip()) > 0:
                    print(f"✅ Quality: Non-empty response")
                else:
                    print(f"❌ Quality: Empty response detected")
                    
            except Exception as e:
                print(f"❌ ERROR: Test failed - {e}")
                logger.exception(f"Test {i} failed")
        
        print("\n" + "=" * 60)
        print("🏁 TEST COMPLETE")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ INITIALIZATION ERROR: {e}")
        logger.exception("Failed to initialize Grok AI")

if __name__ == "__main__":
    test_grok_models()