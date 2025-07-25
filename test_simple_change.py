#!/usr/bin/env python3
"""
Simple test to add one instant response and verify it persists
"""

import os
from admin_action_handler import admin_action_handler

def test_simple_add():
    print("🧪 Testing Simple Instant Response Addition")
    print("=" * 50)
    
    # Test simple addition
    instruction = "when someone says hello respond with hi there"
    print(f"Instruction: {instruction}")
    
    result = admin_action_handler.execute_admin_action(instruction, "+13477430880")
    print(f"Result: {result}")
    
    # Check if the change was written to file
    try:
        with open('fixed_conversation_app.py', 'r') as f:
            content = f.read()
            
        if '"hello": "hi there"' in content:
            print("✅ SUCCESS: Change found in file!")
        else:
            print("❌ FAILURE: Change not found in file")
            print("Looking for: \"hello\": \"hi there\"")
            
            # Show INSTANT_RESPONSES section
            if 'INSTANT_RESPONSES' in content:
                start = content.find('INSTANT_RESPONSES')
                end = content.find('}', start) + 1
                print("Current INSTANT_RESPONSES:")
                print(content[start:end])
            
    except Exception as e:
        print(f"Error checking file: {e}")

if __name__ == "__main__":
    test_simple_add()