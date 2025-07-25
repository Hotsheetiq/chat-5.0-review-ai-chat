#!/usr/bin/env python3
"""
Test interruption capability by checking timeout settings
"""

import re

def check_interruption_settings():
    print("Checking interruption settings in fixed_conversation_app.py...")
    
    with open('fixed_conversation_app.py', 'r') as f:
        content = f.read()
    
    # Find all Gather tags and their timeout settings
    gather_patterns = re.findall(r'<Gather[^>]*timeout="(\d+)"[^>]*speechTimeout="(\d+)"[^>]*>', content)
    
    print(f"Found {len(gather_patterns)} Gather tags:")
    for i, (timeout, speech_timeout) in enumerate(gather_patterns):
        print(f"  {i+1}: timeout={timeout}s, speechTimeout={speech_timeout}s")
        
        if int(speech_timeout) <= 1:
            print(f"    ✅ Good: Short speechTimeout allows interruption")
        else:
            print(f"    ❌ Problem: Long speechTimeout prevents interruption")
    
    return gather_patterns

if __name__ == "__main__":
    check_interruption_settings()