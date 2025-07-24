#!/usr/bin/env python3
"""
Test Rent Manager API with correct lowercase endpoints
"""

import asyncio
import aiohttp
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_correct_endpoints():
    """Test with correct lowercase endpoint names"""
    
    username = os.environ.get('RENT_MANAGER_USERNAME')
    password = os.environ.get('RENT_MANAGER_PASSWORD')
    location_id = os.environ.get('RENT_MANAGER_LOCATION_ID', '1')
    base_url = "https://grinb.api.rentmanager.com"
    
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
                    logger.info(f"✅ Authentication successful")
                else:
                    logger.error(f"❌ Authentication failed: {resp.status}")
                    return
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json", 
                "RentManagerAPIToken": token
            }
            
            # Test correct lowercase endpoints
            test_endpoints = [
                "/tenants",        # Should work based on C# examples
                "/contacts",       # Should work
                "/properties",     # Should work  
                "/units",          # Should work
                "/leases",         # Should work
            ]
            
            working_endpoints = []
            
            for endpoint in test_endpoints:
                try:
                    async with session.get(f"{base_url}{endpoint}", headers=headers, timeout=15) as resp:
                        logger.info(f"🔍 Testing {endpoint}: {resp.status}")
                        
                        if resp.status == 200:
                            logger.info(f"✅ SUCCESS: {endpoint} is accessible!")
                            working_endpoints.append(endpoint)
                            
                            # Get sample data
                            try:
                                data = await resp.json()
                                if isinstance(data, list):
                                    logger.info(f"   📊 Contains {len(data)} records")
                                    if len(data) > 0:
                                        sample = data[0]
                                        if isinstance(sample, dict):
                                            logger.info(f"   🔑 Sample keys: {list(sample.keys())[:8]}")
                                elif isinstance(data, dict):
                                    logger.info(f"   🔑 Keys: {list(data.keys())[:8]}")
                            except Exception as e:
                                logger.info(f"   ⚠️  Could not parse JSON: {e}")
                                
                        elif resp.status == 401:
                            logger.info(f"🔒 UNAUTHORIZED: {endpoint}")
                        elif resp.status == 404:
                            logger.info(f"❌ NOT FOUND: {endpoint}")
                        else:
                            logger.info(f"❓ OTHER STATUS: {endpoint} ({resp.status})")
                            
                except Exception as e:
                    logger.info(f"❌ ERROR testing {endpoint}: {e}")
            
            # If we have working endpoints, try to create a service issue
            if working_endpoints:
                logger.info(f"\n🎯 Found working endpoints: {working_endpoints}")
                
                # Try work order creation endpoints
                work_endpoints = [
                    "/workorders",
                    "/servicerequests", 
                    "/maintenancerequests",
                    "/serviceissues",
                    "/issues"
                ]
                
                for endpoint in work_endpoints:
                    logger.info(f"🔧 Testing work order endpoint: {endpoint}")
                    
                    service_data = {
                        "Description": "Electrical issue - power outage at 29 Port Richmond Avenue",
                        "Category": "Electrical",
                        "Priority": "High",
                        "PropertyID": 1,  # Use property ID 1 as example
                        "Type": "Maintenance"
                    }
                    
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
            
            return {"working_endpoints": working_endpoints}
                    
    except Exception as e:
        logger.error(f"Error: {e}")
        return None

if __name__ == "__main__":
    result = asyncio.run(test_correct_endpoints())
    if result:
        if result.get("success"):
            print(f"\n🎉 SUCCESS! Service issue created in Rent Manager!")
        else:
            print(f"\n📊 Found working data endpoints: {result.get('working_endpoints', [])}")
            print(f"Now we can integrate with real tenant/property data!")
    else:
        print(f"\n❌ Tests failed")