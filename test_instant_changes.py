#!/usr/bin/env python3
"""
Test instant changes to verify they work and stick
"""

from admin_action_handler import admin_action_handler

def test_instant_response():
    print("Testing instant response addition...")
    result = admin_action_handler.execute_admin_action("when someone says test123 respond with working123", "+13477430880")
    print(f"Result: {result}")
    
    # Check if it was written
    with open('fixed_conversation_app.py', 'r') as f:
        content = f.read()
    
    if '"test123": "working123"' in content:
        print("✅ SUCCESS: Instant response was written to file!")
        return True
    else:
        print("❌ FAILURE: Instant response not found in file")
        return False

if __name__ == "__main__":
    test_instant_response()