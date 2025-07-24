#!/usr/bin/env python3
"""
Manual test script for phone lookup functionality.
Run this when API sessions are available to test phone number searches.
"""

import os
import asyncio
from rent_manager import RentManagerAPI

async def test_phone_lookup():
    """Test phone lookup with both known tenant numbers"""
    
    print("=== Phone Lookup Test Script ===")
    print("Testing the rebuilt phone lookup system...")
    
    # Get credentials
    username = os.environ.get('RENT_MANAGER_USERNAME')
    password = os.environ.get('RENT_MANAGER_PASSWORD') 
    location_id = os.environ.get('RENT_MANAGER_LOCATION_ID')
    
    if not all([username, password, location_id]):
        print("❌ Missing Rent Manager credentials")
        return
    
    credentials = f'{username}:{password}:{location_id}'
    rm = RentManagerAPI(credentials)
    
    try:
        print("Authenticating...")
        auth_result = await rm.authenticate()
        
        if not auth_result:
            print("❌ Authentication failed - API session limit reached")
            print("The phone lookup system has been fixed but needs session availability to test")
            return
            
        print("✅ Authenticated successfully")
        
        # Test both phone numbers that should be in the database
        test_numbers = [
            '(347) 743-0880',
            '(347) 265-2556'
        ]
        
        for phone_num in test_numbers:
            print(f"\n🔍 Searching for {phone_num}...")
            
            tenant = await rm.lookup_tenant_by_phone(phone_num)
            
            if tenant:
                print(f"✅ TENANT FOUND!")
                print(f"   Name: {tenant.get('FirstName', '')} {tenant.get('LastName', '')}")
                print(f"   Full Name: {tenant.get('Name', '')}")
                print(f"   Phone: {tenant.get('Phone', '')}")
                print(f"   Unit/Address: {tenant.get('Unit', '')}")
                print(f"   Tenant ID: {tenant.get('TenantID', '')}")
                print(f"   Status: {tenant.get('Status', '')}")
                print(f"   Property ID: {tenant.get('PropertyID', '')}")
            else:
                print(f"❌ {phone_num} not found")
                print(f"   Either not in database or contact detail lookup failed")
        
        print("\n=== Test Complete ===")
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_phone_lookup())