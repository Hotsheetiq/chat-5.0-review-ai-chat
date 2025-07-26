#!/usr/bin/env python3
"""
Improved Address Detection for Speech Recognition Issues
Handles common Twilio speech recognition errors and improves Grok address understanding
"""

import re
import logging

logger = logging.getLogger(__name__)

def fix_speech_recognition_errors(user_input):
    """Fix common speech recognition errors before Grok processes them"""
    
    # Common speech recognition corrections
    speech_corrections = {
        # Address number corrections
        "164 richmond": "2940 richmond",  # Common mishearing
        "46 richmond": "2940 richmond",   # Another variation
        "640 richmond": "2940 richmond",  # Speech variation
        "4640 richmond": "2940 richmond", # Expanded mishearing
        
        # Port Richmond corrections
        "port rich": "port richmond",
        "port richman": "port richmond", 
        "poor richmond": "port richmond",
        
        # Targee corrections
        "target": "targee",
        "targe": "targee",
        "tar-gay": "targee",
        
        # Common word corrections
        "avenue": "avenue",
        "ave": "avenue",
        "street": "street",
        "st": "street",
        
        # Number corrections
        "twenty nine": "29",
        "one twenty two": "122",
        "two nine four zero": "2940",
        "twenty nine forty": "2940",
    }
    
    corrected_input = user_input.lower()
    
    # Apply corrections
    for mistake, correction in speech_corrections.items():
        if mistake in corrected_input:
            corrected_input = corrected_input.replace(mistake, correction)
            logger.info(f"🔧 SPEECH CORRECTION: '{mistake}' → '{correction}'")
    
    return corrected_input

def suggest_closest_address(user_input):
    """Suggest the closest matching address from known properties"""
    
    known_addresses = [
        "29 Port Richmond Avenue",
        "31 Port Richmond Avenue", 
        "122 Targee Street",
        "189 Court Street Richmond",
        "2940 Richmond Avenue",
        "2944 Richmond Avenue",
        "2938 Richmond Avenue"
    ]
    
    # Simple matching based on key words
    input_lower = user_input.lower()
    
    # Check for specific patterns
    if "richmond" in input_lower:
        if any(num in input_lower for num in ["29", "twenty nine"]):
            return "29 Port Richmond Avenue"
        elif any(num in input_lower for num in ["31", "thirty one"]):
            return "31 Port Richmond Avenue"
        elif any(num in input_lower for num in ["2940", "two nine four zero", "164", "46", "640", "4640"]):
            return "2940 Richmond Avenue"
        elif any(num in input_lower for num in ["2944", "two nine four four"]):
            return "2944 Richmond Avenue"
        elif any(num in input_lower for num in ["2938", "two nine three eight"]):
            return "2938 Richmond Avenue"
        elif "court" in input_lower and any(num in input_lower for num in ["189", "one eight nine"]):
            return "189 Court Street Richmond"
    
    if "targee" in input_lower or "target" in input_lower:
        if any(num in input_lower for num in ["122", "one twenty two"]):
            return "122 Targee Street"
    
    # Return None if no clear match
    return None

def enhance_grok_address_understanding(user_input):
    """Prepare user input for better Grok understanding"""
    
    # First fix speech recognition errors
    corrected_input = fix_speech_recognition_errors(user_input)
    
    # Try to find closest address match
    suggested_address = suggest_closest_address(corrected_input)
    
    if suggested_address:
        logger.info(f"🎯 ADDRESS SUGGESTION: '{user_input}' → '{suggested_address}'")
        return suggested_address, corrected_input
    
    return None, corrected_input

if __name__ == "__main__":
    # Test the corrections
    test_inputs = [
        "164 richmond avenue",
        "4640 richmond avenue", 
        "twenty nine port richmond",
        "one twenty two targee",
        "189 court richmond"
    ]
    
    for test in test_inputs:
        suggested, corrected = enhance_grok_address_understanding(test)
        print(f"Input: '{test}' → Suggested: '{suggested}', Corrected: '{corrected}'")