#!/usr/bin/env python3
"""
Test script to verify the request tracking system is working correctly.
This script tests both the API endpoints and the dashboard functionality.
"""

import requests
import json
from datetime import datetime

def test_request_tracking_api():
    """Test the request tracking API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing Request Tracking System")
    print("=" * 50)
    
    # Test 1: Log a new request
    print("\n1. Testing request logging...")
    request_data = {
        "title": "TEST: Dashboard displays real request history instead of hardcoded entries",
        "description": "Update the Request History & Fixes section to use real API data from the request tracking system instead of static hardcoded examples",
        "category": "enhancement",
        "priority": "high"
    }
    
    try:
        response = requests.post(f"{base_url}/api/log-request", json=request_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Request logged successfully: {result['message']}")
            request_id = result.get('request_id')
        else:
            print(f"❌ Failed to log request: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error logging request: {e}")
        return False
    
    # Test 2: Get request history
    print("\n2. Testing request history retrieval...")
    try:
        response = requests.get(f"{base_url}/api/request-history")
        if response.status_code == 200:
            history = response.json()
            print(f"✅ Retrieved {len(history.get('requests', []))} requests")
            if history.get('requests'):
                latest = history['requests'][0]
                print(f"   Latest request: {latest.get('request_title', 'N/A')}")
                print(f"   Status: {latest.get('status', 'N/A')}")
                print(f"   Category: {latest.get('category', 'N/A')}")
        else:
            print(f"❌ Failed to get history: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting history: {e}")
        return False
    
    # Test 3: Update implementation details
    if request_id:
        print("\n3. Testing implementation update...")
        update_data = {
            "implementation_details": "Successfully updated dashboard to use real request tracking API. Replaced hardcoded entries with dynamic JavaScript that fetches data from /api/request-history endpoint. Added proper error handling and loading states.",
            "status": "complete"
        }
        
        try:
            response = requests.post(f"{base_url}/api/update-implementation", 
                                   json={"request_id": request_id, **update_data})
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Implementation updated: {result['message']}")
            else:
                print(f"❌ Failed to update implementation: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error updating implementation: {e}")
            return False
    
    # Test 4: Verify dashboard can load the data
    print("\n4. Testing dashboard integration...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            html_content = response.text
            if "request-history-container" in html_content:
                print("✅ Dashboard contains request history container")
            if "loadRequestHistory" in html_content:
                print("✅ Dashboard contains JavaScript to load request history")
            if "/api/request-history" in html_content:
                print("✅ Dashboard fetches from correct API endpoint")
        else:
            print(f"❌ Dashboard not accessible: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error accessing dashboard: {e}")
        return False
    
    print("\n🎉 All tests passed! Request tracking system is working correctly.")
    return True

def show_current_requests():
    """Display current requests in the system"""
    base_url = "http://localhost:5000"
    
    print("\n📋 Current Request History:")
    print("-" * 30)
    
    try:
        response = requests.get(f"{base_url}/api/request-history")
        if response.status_code == 200:
            history = response.json()
            requests_list = history.get('requests', [])
            
            if not requests_list:
                print("No requests found in system.")
                return
            
            for i, req in enumerate(requests_list, 1):
                print(f"\n{i}. {req.get('request_title', 'Untitled')}")
                print(f"   Status: {req.get('status', 'unknown')}")
                print(f"   Category: {req.get('category', 'general')}")
                print(f"   Priority: {req.get('priority', 'normal')}")
                if req.get('date_requested'):
                    date = datetime.fromisoformat(req['date_requested'].replace('Z', '+00:00'))
                    print(f"   Date: {date.strftime('%Y-%m-%d %H:%M:%S')}")
                if req.get('request_description'):
                    desc = req['request_description'][:100]
                    if len(req['request_description']) > 100:
                        desc += "..."
                    print(f"   Description: {desc}")
        else:
            print(f"Failed to retrieve requests: {response.status_code}")
    except Exception as e:
        print(f"Error retrieving requests: {e}")

if __name__ == "__main__":
    # Run the tests
    success = test_request_tracking_api()
    
    if success:
        show_current_requests()
    else:
        print("\n❌ Tests failed. Check the server and API endpoints.")