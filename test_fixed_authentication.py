#!/usr/bin/env python3
"""
Test Rent Manager API with corrected authentication header and URL
"""

import asyncio
import aiohttp
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_fixed_authentication():
    """Test with correct header name and URL pattern"""
    
    username = os.environ.get('RENT_MANAGER_USERNAME')
    password = os.environ.get('RENT_MANAGER_PASSWORD')
    location_id = os.environ.get('RENT_MANAGER_LOCATION_ID', '1')
    
    # Try both URL patterns
    base_urls = [
        "https://grinb.api.rentmanager.com",  # Current working auth URL
        "https://corporateID.api.rentmanager.com"  # Template from C# code
    ]
    
    for base_url in base_urls:
        logger.info(f"🔍 Testing base URL: {base_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Authenticate
                auth_data = {
                    "Username": username,
                    "Password": password,
                    "LocationID": int(location_id)
                }
                
                async with session.post(f"{base_url}/Authentication/AuthorizeUser", json=auth_data) as resp:
                    if resp.status == 200:
                        token = (await resp.text()).strip('"')
                        logger.info(f"✅ Authentication successful with {base_url}")
                    else:
                        logger.info(f"❌ Authentication failed with {base_url}: {resp.status}")
                        continue
                
                # Test different header formats based on C# code
                header_formats = [
                    {"X-RM12Api-ApiToken": token},  # From C# HttpClientHelper.cs line 32
                    {"RentManagerAPIToken": token}, # What we were using
                    {"X-RentManagerAPIToken": token},
                    {"RM12Api-ApiToken": token}
                ]
                
                for i, auth_header in enumerate(header_formats):
                    headers = {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                    headers.update(auth_header)
                    
                    logger.info(f"🔑 Testing header format {i+1}: {list(auth_header.keys())[0]}")
                    
                    # Test with /tenants endpoint
                    try:
                        async with session.get(f"{base_url}/tenants", headers=headers, timeout=10) as resp:
                            logger.info(f"   /tenants response: {resp.status}")
                            
                            if resp.status == 200:
                                logger.info(f"🎉 SUCCESS! Working authentication found:")
                                logger.info(f"   Base URL: {base_url}")
                                logger.info(f"   Header: {list(auth_header.keys())[0]}")
                                
                                # Test getting tenant data
                                try:
                                    data = await resp.json()
                                    logger.info(f"   📊 Retrieved {len(data)} tenants")
                                    if len(data) > 0:
                                        tenant = data[0]
                                        logger.info(f"   Sample tenant keys: {list(tenant.keys())[:8]}")
                                except Exception as e:
                                    logger.info(f"   Data parsing error: {e}")
                                
                                # Now test service request creation with working auth
                                return await test_service_creation(session, base_url, headers)
                                
                            elif resp.status == 401:
                                logger.info(f"   Still 401 Unauthorized")
                            elif resp.status == 404:
                                logger.info(f"   404 Not Found")
                            else:
                                logger.info(f"   Other status: {resp.status}")
                                
                    except Exception as e:
                        logger.info(f"   Error: {e}")
                        
        except Exception as e:
            logger.error(f"Error with {base_url}: {e}")
    
    return None

async def test_service_creation(session, base_url, headers):
    """Test service request creation with working authentication"""
    
    logger.info(f"🎫 Testing service request creation...")
    
    # Test different service endpoints
    service_endpoints = [
        "/workorders",
        "/servicerequests", 
        "/maintenancerequests",
        "/serviceissues"
    ]
    
    service_data = {
        "Description": "Electrical issue - power outage at 29 Port Richmond Avenue",
        "Category": "Electrical", 
        "Priority": "High",
        "PropertyID": 1,
        "Type": "Maintenance",
        "Source": "Phone Call"
    }
    
    for endpoint in service_endpoints:
        logger.info(f"🔧 Testing {endpoint}...")
        
        try:
            async with session.post(f"{base_url}{endpoint}", headers=headers, json=service_data, timeout=10) as resp:
                logger.info(f"   POST {endpoint}: {resp.status}")
                response_text = await resp.text()
                
                if resp.status in [200, 201]:
                    logger.info(f"🎉 SUCCESS! Created service issue via {endpoint}")
                    logger.info(f"   Response: {response_text}")
                    return {"success": True, "endpoint": endpoint, "response": response_text}
                else:
                    logger.info(f"   Response: {response_text[:200]}")
                    
        except Exception as e:
            logger.info(f"   Error: {e}")
    
    return {"success": False, "message": "No working service endpoints found"}

if __name__ == "__main__":
    result = asyncio.run(test_fixed_authentication())
    if result and result.get("success"):
        print(f"\n🎉 BREAKTHROUGH! Service issue creation working in Rent Manager!")
        print(f"Endpoint: {result['endpoint']}")
        print(f"Response: {result['response']}")
    else:
        print(f"\n❌ Authentication issue persists - may need different API permissions or setup")