#!/usr/bin/env python3
"""
Debug script to test address confirmation logic directly
"""

import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_address_confirmation_logic():
    """Test the exact address confirmation logic from the app"""
    
    # Test inputs that should trigger confirmation
    test_cases = [
        "26 port richmond avenue washing machine",
        "64 port richmond avenue electrical problem",
        "6 port richmond avenue plumbing issue",
        "24 port richmond avenue broken appliance"
    ]
    
    print("🔍 TESTING ADDRESS CONFIRMATION LOGIC DIRECTLY")
    print("="*60)
    
    for test_input in test_cases:
        print(f"\nTesting: '{test_input}'")
        user_lower = test_input.lower()
        
        # Check for address confirmation patterns
        confirmation_pattern = r'(\d{1,3})\s*port\s*richmond'
        match = re.search(confirmation_pattern, user_lower)
        
        if match:
            number = match.group(1)
            print(f"✅ Address pattern matched: number='{number}'")
            
            # This is the exact logic from the app
            if number not in ['29', '31']:
                if number in ['26', '64', '24', '28', '6', 'funny', '16']:
                    print(f"✅ SHOULD TRIGGER CONFIRMATION: '{number}' Port Richmond")
                    confirmation_response = f"I heard {number} Port Richmond Avenue but couldn't find that exact address. Did you mean 29 Port Richmond Avenue or 31 Port Richmond Avenue?"
                    print(f"📱 Confirmation message: {confirmation_response}")
                    
                    # Check if this would be detected as address confirmation request
                    return True
                else:
                    print(f"❌ Number '{number}' not in known confirmation list")
            else:
                print(f"ℹ️ Valid address number '{number}' - no confirmation needed")
        else:
            print("❌ No address pattern detected")
        
        print("-" * 40)
    
    return False

def check_instant_patterns():
    """Check if these are being caught by instant patterns"""
    
    instant_patterns = {
        "appliance": "What appliance issue? I can help create a service ticket.",
        "washing machine": "Washing machine issue! What's your address?",
        "washer": "Washing machine issue! What's your address?",
        "dryer": "Dryer issue! What's your address?",
        "dishwasher": "Dishwasher issue! What's your address?",
        
        # Electrical issues - PRIORITY RESPONSES
        "electrical": "Electrical issue! What's your address?",
        "electric": "Electrical issue! What's your address?",
        "power": "Electrical issue! What's your address?",
        "electricity": "Electrical issue! What's your address?",
        "no power": "Electrical emergency! What's your address?",
        "lights": "Electrical issue! What's your address?",
        "outlet": "Electrical issue! What's your address?",
    }
    
    test_inputs = [
        "26 port richmond avenue washing machine",
        "64 port richmond avenue electrical problem", 
        "6 port richmond avenue plumbing issue"
    ]
    
    print(f"\n{'='*60}")
    print("🚀 CHECKING INSTANT PATTERN MATCHES")
    print("="*60)
    
    for test_input in test_inputs:
        user_lower = test_input.lower()
        print(f"\nTesting: '{test_input}'")
        
        matched_patterns = []
        for pattern, response in instant_patterns.items():
            if pattern in user_lower:
                matched_patterns.append((pattern, response))
        
        if matched_patterns:
            print(f"✅ INSTANT PATTERNS MATCHED:")
            for pattern, response in matched_patterns:
                print(f"   - '{pattern}' → '{response}'")
        else:
            print("❌ No instant patterns matched")

if __name__ == "__main__":
    test_address_confirmation_logic()
    check_instant_patterns()
    
    print(f"\n{'='*60}")
    print("🎯 DEBUG SUMMARY:")
    print("1. Address confirmation logic should detect invalid addresses")
    print("2. But instant patterns might be catching these first")
    print("3. Need to check pattern priority in actual app")
    print("="*60)