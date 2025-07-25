#!/usr/bin/env python3
"""
Debug pattern matching for admin actions
"""

import re

def test_patterns():
    patterns = [
        r"when someone says\s+(.+?)\s+respond\s+with\s+(.+)",
        r"when.*says?\s+(.+?)\s+respond.*with\s+(.+)",
        r"add.*response.*for\s+(.+?):\s*(.+)",
        r"if.*says?\s+(.+?)\s+say\s+(.+)",
        r"says?\s+(.+?)\s+respond.*with\s+(.+)"
    ]
    
    test_inputs = [
        "when someone says hello respond with hi there",
        "when someone says hello chris respond with Hi there! I'm Chris!",
        "add response for good morning: Good morning! How can I help?",
        "if someone says thank you say You're welcome!",
        "says hello respond with hi"
    ]
    
    for instruction in test_inputs:
        print(f"\nTesting: '{instruction}'")
        found_match = False
        
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, instruction, re.IGNORECASE)
            if match and len(match.groups()) >= 2:
                trigger = match.group(1).lower().strip()
                response = match.group(2).strip()
                trigger = trigger.strip('\'"')
                response = response.strip('\'"')
                print(f"  Pattern {i+1} MATCHED: '{trigger}' -> '{response}'")
                found_match = True
                break
        
        if not found_match:
            print("  No pattern matched")

if __name__ == "__main__":
    test_patterns()