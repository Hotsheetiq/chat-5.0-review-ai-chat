#!/usr/bin/env python3
"""
Test Admin Training System - Direct demonstration of functionality
"""

import sys
from admin_action_handler import admin_action_handler

def test_admin_actions():
    """Test the admin action handler directly"""
    print("🧪 Testing Admin Training System")
    print("=" * 50)
    
    # Test 1: Add instant response
    print("\n1. Testing: Add instant response")
    instruction1 = "When someone says hello chris respond with Hi there! I'm Chris!"
    result1 = admin_action_handler.execute_admin_action(instruction1, "+13477430880")
    print(f"Input: {instruction1}")
    print(f"Result: {result1}")
    
    # Test 2: Change greeting
    print("\n2. Testing: Change greeting")
    instruction2 = "Change greeting to say Welcome to Grinberg Management!"
    result2 = admin_action_handler.execute_admin_action(instruction2, "+13477430880")
    print(f"Input: {instruction2}")
    print(f"Result: {result2}")
    
    # Test 3: Pattern variations
    print("\n3. Testing: Pattern variations")
    variations = [
        "add response for good morning: Good morning! How can I help?",
        "if someone says thank you say You're welcome!",
        "modify greeting to be more friendly",
        "update greeting to say Hello and welcome!"
    ]
    
    for variation in variations:
        result = admin_action_handler.execute_admin_action(variation, "+13477430880")
        print(f"Input: {variation}")
        print(f"Result: {result}")
        print()

if __name__ == "__main__":
    test_admin_actions()