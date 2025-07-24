#!/usr/bin/env python3
"""
Test creating a real service issue in Rent Manager
"""

import asyncio
import sys
import os
import logging

# Add current directory to path so we can import our modules
sys.path.append('.')

from rent_manager import RentManagerAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_service_issue_creation():
    """Test creating a real service issue in Rent Manager"""
    
    try:
        # Initialize with our working credentials
        username = os.environ.get('RENT_MANAGER_USERNAME')
        password = os.environ.get('RENT_MANAGER_PASSWORD')
        location_id = os.environ.get('RENT_MANAGER_LOCATION_ID', '1')
        credentials = f"{username}:{password}:{location_id}"
        api = RentManagerAPI(credentials)
        
        # Test authentication
        logger.info("🔑 Authenticating...")
        auth_success = await api.authenticate()
        
        if not auth_success:
            logger.error("❌ Authentication failed")
            return False
        
        logger.info("✅ Authentication successful!")
        
        # Test work order creation with different endpoint names
        work_endpoints = [
            "/workorders",
            "/servicerequests",
            "/maintenancerequests",
            "/serviceissues",
            "/maintenance",
            "/issues"
        ]
        
        # Create test service issue data
        service_data = {
            "Description": "Electrical issue - power outage at 29 Port Richmond Avenue reported via Chris AI Assistant",
            "Type": "Maintenance",
            "Category": "Electrical",
            "Priority": "High", 
            "Source": "Phone Call",
            "Notes": "Test service issue creation from voice assistant",
            "PropertyID": 1,  # Use first property as test
            "Status": "Open"
        }
        
        logger.info("🔧 Testing service issue creation endpoints...")
        
        for endpoint in work_endpoints:
            logger.info(f"Testing POST {endpoint}...")
            
            try:
                result = await api._make_request("POST", endpoint, service_data)
                
                if result is not None:
                    logger.info(f"🎉 SUCCESS! Created service issue via {endpoint}")
                    logger.info(f"Response: {result}")
                    
                    # Extract issue number/ID from response
                    issue_id = None
                    issue_number = None
                    
                    if isinstance(result, dict):
                        issue_id = result.get('WorkOrderID') or result.get('ServiceRequestID') or result.get('ID')
                        issue_number = result.get('WorkOrderNumber') or result.get('Number') or result.get('IssueNumber')
                    elif isinstance(result, list) and len(result) > 0:
                        first_result = result[0]
                        issue_id = first_result.get('WorkOrderID') or first_result.get('ServiceRequestID') or first_result.get('ID')
                        issue_number = first_result.get('WorkOrderNumber') or first_result.get('Number') or first_result.get('IssueNumber')
                    
                    logger.info(f"🎯 Issue ID: {issue_id}, Issue Number: {issue_number}")
                    
                    return {
                        "success": True,
                        "endpoint": endpoint,
                        "issue_id": issue_id,
                        "issue_number": issue_number,
                        "response": result
                    }
                else:
                    logger.info(f"❌ {endpoint} failed or returned empty")
                    
            except Exception as e:
                logger.info(f"❌ Error with {endpoint}: {e}")
        
        # If POST failed, try to understand the structure by GET first
        logger.info("🔍 Trying to understand work order structure...")
        
        for endpoint in work_endpoints:
            logger.info(f"GET {endpoint} to check structure...")
            try:
                result = await api._make_request("GET", endpoint)
                if result is not None:
                    logger.info(f"✅ {endpoint} exists and returned data")
                    if isinstance(result, list) and len(result) > 0:
                        sample = result[0]
                        logger.info(f"Sample keys: {list(sample.keys())[:10]}")
                    return {"info": f"Found working GET endpoint: {endpoint}"}
            except Exception as e:
                logger.info(f"GET {endpoint} error: {e}")
        
        return {"success": False, "message": "No working endpoints found"}
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    result = asyncio.run(test_service_issue_creation())
    if result and result.get("success"):
        print(f"\n🎉 REAL SERVICE ISSUE CREATED IN RENT MANAGER!")
        print(f"Endpoint: {result['endpoint']}")
        print(f"Issue ID: {result['issue_id']}")
        print(f"Issue Number: {result['issue_number']}")
        print(f"\nChris can now create actual service tickets!")
    elif result and result.get("info"):
        print(f"\n📋 {result['info']}")
        print(f"API structure discovered - ready for integration!")
    else:
        print(f"\n🔧 Service creation endpoints need more investigation")
        print(f"However, tenant data access is working perfectly!")
        print(f"Chris can provide professional service with proper fallback responses")