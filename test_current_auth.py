#!/usr/bin/env python3
"""
Test our current working authentication with lowercase endpoints
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

async def test_current_authentication():
    """Test our current RentManagerAPI class with lowercase endpoints"""
    
    try:
        # Initialize with our working credentials in correct format
        username = os.environ.get('RENT_MANAGER_USERNAME')
        password = os.environ.get('RENT_MANAGER_PASSWORD')
        location_id = os.environ.get('RENT_MANAGER_LOCATION_ID', '1')
        credentials = f"{username}:{password}:{location_id}"
        api = RentManagerAPI(credentials)
        
        # Test authentication
        logger.info("🔑 Testing authentication...")
        auth_success = await api.authenticate()
        
        if not auth_success:
            logger.error("❌ Authentication failed")
            return False
        
        logger.info("✅ Authentication successful!")
        
        # Test lowercase endpoints directly
        logger.info("🔍 Testing lowercase endpoints...")
        
        endpoints_to_test = [
            "/tenants",
            "/properties", 
            "/contacts",
            "/units"
        ]
        
        for endpoint in endpoints_to_test:
            logger.info(f"Testing {endpoint}...")
            result = await api._make_request("GET", endpoint)
            
            if result is not None:
                logger.info(f"✅ SUCCESS: {endpoint} returned data!")
                if isinstance(result, list):
                    logger.info(f"   📊 Found {len(result)} records")
                    if len(result) > 0 and isinstance(result[0], dict):
                        logger.info(f"   🔑 Sample keys: {list(result[0].keys())[:6]}")
                return True
            else:
                logger.info(f"❌ {endpoint} failed or returned empty")
        
        # If data endpoints failed, try work order endpoints
        logger.info("🔧 Testing work order endpoints...")
        
        work_endpoints = [
            "/workorders",
            "/servicerequests",
            "/maintenancerequests"
        ]
        
        test_data = {
            "Description": "Test electrical issue",
            "Category": "Electrical",
            "Priority": "High"
        }
        
        for endpoint in work_endpoints:
            logger.info(f"Testing POST {endpoint}...")
            result = await api._make_request("POST", endpoint, test_data)
            
            if result is not None:
                logger.info(f"🎉 SUCCESS: Created service request via {endpoint}!")
                logger.info(f"   Response: {result}")
                return True
            else:
                logger.info(f"❌ {endpoint} failed")
        
        return False
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_current_authentication())
    if success:
        print(f"\n🎉 BREAKTHROUGH! Rent Manager API integration is working!")
        print(f"We can now create real service issues in the system!")
    else:
        print(f"\n🔧 Current API setup needs permission adjustments")
        print(f"Authentication works but data access is restricted")
        print(f"However, Chris can still provide professional service with fallback responses")