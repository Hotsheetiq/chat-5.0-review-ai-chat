#!/usr/bin/env python3
"""
Test script to create a service issue for 29 Port Richmond Avenue
This will verify the Rent Manager API integration is working properly.
"""

import sys
import os
sys.path.append('.')

from service_issue_handler import ServiceIssueHandler
from rent_manager import RentManagerAPI
import logging
import os
import asyncio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_create_service_issue():
    """Test creating a service issue for 29 Port Richmond Avenue"""
    
    try:
        # Format credentials as expected by RentManagerAPI (string format)
        username = os.environ.get('RENT_MANAGER_USERNAME')
        password = os.environ.get('RENT_MANAGER_PASSWORD')
        location_id = os.environ.get('RENT_MANAGER_LOCATION_ID', '1')
        
        credentials = f"{username}:{password}:{location_id}"
        
        # Initialize the rent manager API and service handler
        rent_manager = RentManagerAPI(credentials)
        service_handler = ServiceIssueHandler(rent_manager)
        logger.info("🔧 Creating test electrical service issue for 29 Port Richmond Avenue")
        
        # Create a mock tenant info for the test
        tenant_info = {
            'TenantID': 'TEST001',
            'Name': 'Test Tenant',
            'Unit': '29 Port Richmond Avenue',
            'Phone': '+13477430880'
        }
        
        # Create the service issue using the correct method
        result = asyncio.run(service_handler.create_maintenance_issue(
            tenant_info=tenant_info,
            issue_type="electrical",
            description="Test electrical issue - power outage reported by tenant via phone system",
            unit_address="29 Port Richmond Avenue"
        ))
        
        if result and 'issue_number' in result:
            logger.info(f"✅ SUCCESS! Created service issue #{result['issue_number']}")
            logger.info(f"📋 Issue Details: {result}")
            print(f"\n🎫 SERVICE ISSUE CREATED SUCCESSFULLY!")
            print(f"Issue Number: #{result['issue_number']}")
            print(f"Address: 29 Port Richmond Avenue")
            print(f"Type: Electrical")
            print(f"Priority: High")
            print(f"Assigned to: Dimitry Simanovsky")
            print(f"\nCheck Rent Manager for this issue under 29 Port Richmond Avenue!")
            return result
        else:
            logger.error(f"❌ FAILED: No issue number returned. Result: {result}")
            print(f"\n❌ FAILED TO CREATE SERVICE ISSUE")
            print(f"Result: {result}")
            return None
            
    except Exception as e:
        logger.error(f"❌ ERROR creating service issue: {e}")
        print(f"\n❌ ERROR: {e}")
        return None

if __name__ == "__main__":
    test_create_service_issue()