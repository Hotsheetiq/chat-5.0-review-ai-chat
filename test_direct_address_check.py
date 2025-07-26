#!/usr/bin/env python3
"""
Direct test to debug why address confirmation isn't working
"""

import re

def test_regex_pattern():
    """Test the regex pattern directly"""
    pattern = r'(\d{1,3})\s*port\s*richmond'
    
    test_inputs = [
        "26 port richmond avenue washing machine",
        "64 port richmond avenue electrical problem", 
        "6 port richmond avenue plumbing issue",
        "washing machine 24 port richmond",
        "funny 6. port richmondmond avenue."  # From the actual logs
    ]
    
    print("🔍 TESTING REGEX PATTERN DIRECTLY")
    print(f"Pattern: {pattern}")
    print("="*60)
    
    for test_input in test_inputs:
        user_lower = test_input.lower()
        match = re.search(pattern, user_lower)
        
        print(f"Input: '{test_input}'")
        print(f"Lower: '{user_lower}'")
        
        if match:
            number = match.group(1)
            print(f"✅ MATCH FOUND: number='{number}'")
            
            if number not in ['29', '31']:
                if number in ['26', '64', '24', '28', '6', 'funny', '16']:
                    print(f"✅ SHOULD TRIGGER CONFIRMATION for '{number}'")
                else:
                    print(f"❌ Number '{number}' not in confirmation list")
            else:
                print(f"ℹ️ Valid number '{number}' - no confirmation needed")
        else:
            print("❌ NO MATCH")
            
        print("-" * 40)

def test_speech_corrections():
    """Test what speech corrections are doing"""
    speech_fixes = [
        ("164 richmond", "2940 richmond"),
        ("4640 richmond", "2940 richmond"), 
        ("46 richmond", "2940 richmond"),
        ("640 richmond", "2940 richmond"),
        ("19640 richmond", "2940 richmond"),
        ("192940 richmond", "2940 richmond"),
        ("port rich", "port richmond"),
        ("poor richmond", "port richmond"),
        ("target", "targee"),
        ("targe", "targee"),
        ("twenty nine", "29"),
        ("one twenty two", "122")
    ]
    
    print("\n🔧 TESTING SPEECH CORRECTIONS")
    print("="*60)
    
    test_inputs = [
        "26 port richmond avenue washing machine",
        "64 port richmond avenue electrical problem"
    ]
    
    for user_input in test_inputs:
        user_lower = user_input.lower()
        corrected = user_lower
        
        print(f"Original: '{user_input}'")
        
        for mistake, correction in speech_fixes:
            if mistake in corrected:
                corrected = corrected.replace(mistake, correction)
                print(f"🔧 CORRECTION: '{mistake}' → '{correction}'")
                print(f"Result: '{corrected}'")
                break
        
        if corrected == user_lower:
            print("ℹ️ No speech corrections applied")
        
        print("-" * 40)

if __name__ == "__main__":
    test_regex_pattern()
    test_speech_corrections()