#!/usr/bin/env python3
"""
Test Today's Data Visibility
Make sure today's calls and logs are showing up properly in dashboard
"""

import requests
import json
from datetime import datetime

def test_todays_data():
    """Test that today's data is visible in the dashboard"""
    
    base_url = "http://0.0.0.0:5000"
    today = datetime.now().strftime('%Y-%m-%d')
    today_full = datetime.now().strftime('%B %d, %Y')
    
    print("🗓️ TODAY'S DATA VISIBILITY TEST")
    print(f"Looking for data from: {today} ({today_full})")
    print("=" * 60)
    
    # Test 1: Create a new log entry to see if today's date formats correctly
    print("1. CREATING NEW LOG ENTRY")
    print("-" * 30)
    
    try:
        log_data = {
            'request': 'Test dashboard data visibility for today\'s date',
            'resolution': 'Testing that new logs show today\'s date correctly'
        }
        
        response = requests.post(f"{base_url}/api/auto-log-request", 
                               json=log_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✅ New log created: Log #{result.get('log_id', 'Unknown')}")
            else:
                print(f"❌ Log creation failed: {result.get('message', 'Unknown error')}")
        else:
            print(f"❌ Log creation request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Log creation error: {e}")
    
    # Test 2: Check call history for today's calls
    print(f"\n2. CHECKING TODAY'S CALL HISTORY ({today})")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/call-history", timeout=10)
        
        if response.status_code == 200:
            calls = response.json()
            todays_calls = [call for call in calls if call.get('timestamp', '').startswith(today)]
            
            print(f"Total calls in history: {len(calls)}")
            print(f"Today's calls: {len(todays_calls)}")
            
            if todays_calls:
                print("\nRecent today's calls:")
                for i, call in enumerate(todays_calls[:3]):
                    timestamp = call.get('timestamp', '')[:16]  # Just date and hour
                    phone = call.get('caller_phone', 'Unknown')
                    print(f"  {i+1}. {timestamp} - {phone}")
            else:
                print("⚠️ No calls found for today")
                
        else:
            print(f"❌ Call history request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Call history error: {e}")
    
    # Test 3: Check unified logs for today's entries
    print(f"\n3. CHECKING TODAY'S LOG ENTRIES ({today_full})")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/unified-logs", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('unified_logs', [])
            
            todays_logs = [log for log in logs if today_full in log.get('date', '')]
            august_logs = [log for log in logs if 'August' in log.get('date', '')]
            july_logs = [log for log in logs if 'July' in log.get('date', '')]
            
            print(f"Total logs: {len(logs)}")
            print(f"Today's logs ({today_full}): {len(todays_logs)}")
            print(f"August logs: {len(august_logs)}")
            print(f"July logs: {len(july_logs)}")
            
            if todays_logs:
                print(f"\nToday's log entries:")
                for log in todays_logs[:3]:
                    print(f"  - {log.get('date', '')} at {log.get('time', '')}")
                    print(f"    {log.get('request', '')[:50]}...")
            else:
                print(f"⚠️ No logs found for today ({today_full})")
                
            # Show most recent logs regardless of date
            print(f"\nMost recent logs (any date):")
            for log in logs[-3:]:
                date = log.get('date', '')
                request = log.get('request', '')[:40]
                print(f"  - {date}: {request}...")
                
        else:
            print(f"❌ Unified logs request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Unified logs error: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 TODAY'S DATA VISIBILITY TEST COMPLETE")

if __name__ == "__main__":
    test_todays_data()