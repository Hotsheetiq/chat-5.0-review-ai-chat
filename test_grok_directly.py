#!/usr/bin/env python3
"""Test Grok AI directly to see if it improves conversation memory"""

import sys
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_grok_conversation_memory():
    try:
        from grok_integration import GrokAI
        
        # Initialize Grok
        grok = GrokAI()
        print("✅ Grok AI initialized successfully")
        
        # Test conversation memory scenario
        messages = [
            {
                "role": "system",
                "content": "You are Chris, a property management AI assistant. Remember conversation context and maintain memory across responses."
            },
            {
                "role": "user", 
                "content": "Hi Chris, my washing machine is broken"
            },
            {
                "role": "assistant",
                "content": "I understand you have a washing machine issue. What's your property address so I can create a service ticket?"
            },
            {
                "role": "user",
                "content": "29 Port Richmond Avenue"
            }
        ]
        
        # Test Grok response
        print("\n🧠 Testing Grok conversation memory...")
        response = grok.generate_response(
            messages=messages,
            max_tokens=200,
            temperature=0.7,
            timeout=5.0
        )
        
        print(f"🤖 GROK RESPONSE: {response}")
        
        # Test context analysis
        print("\n🔍 Testing Grok context analysis...")
        conversation_history = [
            {"role": "user", "content": "my washing machine is broken"},
            {"role": "assistant", "content": "What's your address?"},
            {"role": "user", "content": "29 Port Richmond Avenue"}
        ]
        
        context = grok.analyze_conversation_context(conversation_history)
        print(f"📊 CONTEXT ANALYSIS: {context}")
        
        return True
        
    except Exception as e:
        logger.error(f"Grok test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_grok_conversation_memory()
    if success:
        print("\n✅ Grok AI is working properly")
    else:
        print("\n❌ Grok AI test failed")
        sys.exit(1)