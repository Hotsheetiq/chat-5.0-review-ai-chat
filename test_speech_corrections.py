#!/usr/bin/env python3
"""
Test speech recognition corrections for common Twilio mishearing patterns
"""

def test_speech_corrections():
    """Test the speech correction patterns"""
    
    # Common mishearing patterns
    test_cases = [
        # "25" heard as "2540"
        ("2540 port richmond", "25 port richmond"),
        ("2540 richmond avenue", "25 richmond avenue"),
        ("I live at 2540 Port Richmond", "I live at 25 Port Richmond"),
        
        # "29" heard as "290" 
        ("290 port richmond", "29 port richmond"),
        
        # "31" heard as "310"
        ("310 port richmond", "31 port richmond"),
        
        # "122" heard as "1220" or "1225"
        ("1220 targee street", "122 targee street"),
        ("1225 targee", "122 targee"),
    ]
    
    # Speech correction patterns from the app
    speech_fixes = [
        ("2540 port richmond", "25 port richmond"),
        ("2540 richmond", "25 richmond"),  
        ("254 port richmond", "25 port richmond"),
        ("250 port richmond", "25 port richmond"),
        ("290 port richmond", "29 port richmond"),
        ("310 port richmond", "31 port richmond"),
        ("1220 targee", "122 targee"),
        ("1225 targee", "122 targee"),
    ]
    
    print("=== Speech Recognition Correction Tests ===")
    
    for original, expected in test_cases:
        corrected = original.lower()
        
        # Apply speech fixes
        for error_pattern, correction in speech_fixes:
            if error_pattern in corrected:
                corrected = corrected.replace(error_pattern, correction)
                break
        
        print(f"Original: '{original}'")
        print(f"Expected: '{expected}'")
        print(f"Corrected: '{corrected}'")
        
        if expected.lower() in corrected:
            print("✅ PASS")
        else:
            print("❌ FAIL")
        print("-" * 50)

if __name__ == "__main__":
    test_speech_corrections()