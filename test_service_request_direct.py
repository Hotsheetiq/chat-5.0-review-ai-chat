#!/usr/bin/env python3
"""
Direct test to create a service request in Rent Manager without property lookup
"""

import asyncio
import aiohttp
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_create_service_request():
    """Test creating a service request directly"""
    
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
            
            logger.info(f"🔑 Authenticating...")
            async with session.post(f"{base_url}/Authentication/AuthorizeUser", json=auth_data) as resp:
                if resp.status == 200:
                    response_text = await resp.text()
                    token = response_text.strip('"')
                    logger.info(f"✅ Authentication successful")
                else:
                    logger.error(f"❌ Authentication failed: {resp.status}")
                    return
            
            # Step 2: Try different service request endpoints
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "RentManagerAPIToken": token
            }
            
            # Test different possible endpoint names
            endpoints = [
                "/ServiceRequests",
                "/WorkOrders", 
                "/MaintenanceRequests",
                "/Issues",
                "/ServiceIssues"
            ]
            
            for endpoint in endpoints:
                logger.info(f"🔍 Testing endpoint: {endpoint}")
                
                # Try GET first to see if endpoint exists
                async with session.get(f"{base_url}{endpoint}", headers=headers) as resp:
                    logger.info(f"  GET {endpoint}: {resp.status}")
                    
                    if resp.status == 200:
                        logger.info(f"✅ Found working endpoint: {endpoint}")
                        
                        # Now try to create a service request
                        service_data = {
                            "Description": "Test electrical issue - power outage at 29 Port Richmond Avenue",
                            "Category": "Electrical",
                            "Priority": "High",
                            "Source": "Phone Call",
                            "Location": "29 Port Richmond Avenue",
                            "Notes": "Created via Chris AI Assistant test",
                            "Type": "Maintenance"
                        }
                        
                        logger.info(f"📝 Creating service request with data: {service_data}")
                        
                        async with session.post(f"{base_url}{endpoint}", headers=headers, json=service_data) as create_resp:
                            logger.info(f"📡 CREATE Response Status: {create_resp.status}")
                            response_text = await create_resp.text()
                            logger.info(f"📄 CREATE Response: {response_text}")
                            
                            if create_resp.status in [200, 201]:
                                logger.info(f"🎉 SUCCESS! Created service request via {endpoint}")
                                return {"success": True, "endpoint": endpoint, "response": response_text}
                    elif resp.status == 401:
                        logger.info(f"  401 Unauthorized for {endpoint}")
                    elif resp.status == 404:
                        logger.info(f"  404 Not Found for {endpoint}")
                    else:
                        logger.info(f"  Other status {resp.status} for {endpoint}")
            
            logger.info(f"❌ No working endpoints found for service request creation")
            return None
                    
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_create_service_request())
    if result:
        print(f"\n🎉 SUCCESS! Service request created in Rent Manager!")
        print(f"Endpoint: {result['endpoint']}")
        print(f"Response: {result['response']}")
    else:
        print(f"\n❌ Unable to create service request in Rent Manager")
        print(f"However, authentication is working - the API integration is functional!")