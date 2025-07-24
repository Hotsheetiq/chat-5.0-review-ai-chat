#!/usr/bin/env python3
"""
Direct test of Rent Manager API to create a service issue
"""

import asyncio
import aiohttp
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rent_manager_direct():
    """Test creating a service issue directly with Rent Manager API"""
    
    # Get credentials
    username = os.environ.get('RENT_MANAGER_USERNAME')
    password = os.environ.get('RENT_MANAGER_PASSWORD')
    location_id = os.environ.get('RENT_MANAGER_LOCATION_ID', '1')
    
    base_url = "https://grinb.api.rentmanager.com"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Authenticate
            auth_data = {
                "Username": username,
                "Password": password,
                "LocationID": int(location_id)
            }
            
            logger.info(f"🔑 Authenticating with Rent Manager...")
            async with session.post(f"{base_url}/Authentication/AuthorizeUser", json=auth_data) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    logger.info(f"📄 Auth response: {response_text}")
                    
                    # The response might be a plain string token, not JSON
                    if response_text.startswith('"') and response_text.endswith('"'):
                        token = response_text.strip('"')
                    else:
                        token = response_text.strip()
                    
                    logger.info(f"✅ Authentication successful, token: {token[:20]}...")
                else:
                    logger.error(f"❌ Authentication failed: {resp.status}")
                    response_text = await resp.text()
                    logger.error(f"Error response: {response_text}")
                    return
            
            # Step 2: Look up properties to find 29 Port Richmond Avenue  
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "RentManagerAPIToken": token
            }
            logger.info(f"🏠 Looking up properties for 29 Port Richmond Avenue...")
            logger.info(f"🔑 Using headers: {headers}")
            
            async with session.get(f"{base_url}/Properties", headers=headers) as resp:
                if resp.status == 200:
                    properties = await resp.json()
                    logger.info(f"📋 Found {len(properties)} properties")
                    
                    # Look for 29 Port Richmond Avenue
                    target_property = None
                    for prop in properties:
                        if "29" in str(prop.get('Name', '')) and "port richmond" in str(prop.get('Name', '')).lower():
                            target_property = prop
                            logger.info(f"🎯 Found target property: {prop}")
                            break
                    
                    if not target_property:
                        logger.info(f"🔍 Property not found by name, checking all properties...")
                        for prop in properties[:5]:  # Show first 5 properties
                            logger.info(f"   Property: {prop.get('Name')} - ID: {prop.get('PropertyID')}")
                else:
                    logger.error(f"❌ Failed to get properties: {resp.status}")
                    return
            
            # Step 3: Try to create a service issue
            logger.info(f"🎫 Attempting to create service issue...")
            
            service_data = {
                "PropertyID": target_property.get('PropertyID') if target_property else 1,
                "Description": "Test electrical issue - power outage at 29 Port Richmond Avenue",
                "Category": "Electrical",
                "Priority": "High",
                "Source": "Phone Call",
                "Notes": "Created via Chris AI Assistant test"
            }
            
            logger.info(f"📝 Service issue data: {service_data}")
            
            async with session.post(f"{base_url}/ServiceRequests", headers=headers, json=service_data) as resp:
                logger.info(f"📡 API Response Status: {resp.status}")
                response_text = await resp.text()
                logger.info(f"📄 API Response: {response_text}")
                
                if resp.status in [200, 201]:
                    result = await resp.json() if response_text else {}
                    logger.info(f"✅ Service issue created successfully: {result}")
                    return result
                else:
                    logger.error(f"❌ Failed to create service issue: {resp.status} - {response_text}")
                    return None
                    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_rent_manager_direct())
    if result:
        print(f"\n🎉 SUCCESS! Service issue created in Rent Manager!")
        print(f"Details: {result}")
    else:
        print(f"\n❌ No service issue was created in Rent Manager")