#!/usr/bin/env python3
"""
Quick script to check recent call activity and conversation history
"""
import requests
import json

def check_recent_activity():
    print("Checking recent call activity...")
    
    # Check if there are any active conversations stored
    try:
        # Try to make a test call to see current conversation state
        response = requests.get("http://0.0.0.0:5000/")
        if "Active calls: " in response.text:
            print("✅ Application is running and responsive")
            
            # Extract call count
            import re
            call_match = re.search(r'Active calls: (\d+)', response.text)
            conv_match = re.search(r'Total conversations: (\d+)', response.text)
            
            if call_match and conv_match:
                print(f"📞 Active calls: {call_match.group(1)}")
                print(f"💬 Total conversations: {conv_match.group(1)}")
            
        else:
            print("❌ Application not responding properly")
            
    except Exception as e:
        print(f"❌ Error checking application: {e}")

if __name__ == "__main__":
    check_recent_activity()