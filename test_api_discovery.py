#!/usr/bin/env python3
"""
Discover available Rent Manager API endpoints
"""

import asyncio
import aiohttp
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def discover_api_endpoints():
    """Discover what endpoints are available in the Rent Manager API"""
    
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
                    logger.info(f"Authentication successful")
                else:
                    logger.error(f"Authentication failed: {resp.status}")
                    return
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json", 
                "RentManagerAPIToken": token
            }
            
            # Test endpoints that might exist based on common patterns
            test_endpoints = [
                # From documentation or common REST patterns
                "/Help",
                "/Help/Api",
                "/Help/Resources", 
                "/api",
                "/api/help",
                
                # Data endpoints
                "/Tenants",
                "/Contacts", 
                "/Units",
                "/Properties",
                "/Leases",
                
                # Work order / service endpoints
                "/WorkOrders",
                "/ServiceRequests", 
                "/MaintenanceRequests",
                "/Issues",
                "/Tasks", 
                "/Activities",
                "/Notes",
                "/Communications",
                
                # Other possibilities
                "/Categories",
                "/Priorities",
                "/Users",
                "/Vendors"
            ]
            
            working_endpoints = []
            
            for endpoint in test_endpoints:
                try:
                    async with session.get(f"{base_url}{endpoint}", headers=headers, timeout=10) as resp:
                        status = resp.status
                        if status == 200:
                            logger.info(f"✅ WORKING: {endpoint} (200 OK)")
                            working_endpoints.append(endpoint)
                            
                            # Try to get a sample of the data
                            try:
                                data = await resp.json()
                                if isinstance(data, list):
                                    logger.info(f"   Contains {len(data)} items")
                                    if len(data) > 0 and isinstance(data[0], dict):
                                        sample_keys = list(data[0].keys())[:5]
                                        logger.info(f"   Sample keys: {sample_keys}")
                                elif isinstance(data, dict):
                                    logger.info(f"   Keys: {list(data.keys())[:10]}")
                            except:
                                logger.info(f"   Response data not JSON parseable")
                                
                        elif status == 401:
                            logger.info(f"🔒 UNAUTHORIZED: {endpoint} (401)")
                        elif status == 404:
                            logger.info(f"❌ NOT FOUND: {endpoint} (404)")
                        elif status == 405:
                            logger.info(f"⚠️  METHOD NOT ALLOWED: {endpoint} (405) - endpoint exists but GET not allowed")
                            working_endpoints.append(f"{endpoint} (POST only)")
                        else:
                            logger.info(f"❓ OTHER: {endpoint} ({status})")
                            
                except asyncio.TimeoutError:
                    logger.info(f"⏰ TIMEOUT: {endpoint}")
                except Exception as e:
                    logger.info(f"❌ ERROR: {endpoint} - {e}")
            
            logger.info(f"\n🎯 SUMMARY OF WORKING ENDPOINTS:")
            for endpoint in working_endpoints:
                logger.info(f"   {endpoint}")
            
            return working_endpoints
                    
    except Exception as e:
        logger.error(f"Error: {e}")
        return []

if __name__ == "__main__":
    working = asyncio.run(discover_api_endpoints())
    print(f"\n📋 DISCOVERED WORKING ENDPOINTS:")
    for endpoint in working:
        print(f"  {endpoint}")
    
    if not working:
        print(f"\n❌ No accessible endpoints found")
        print(f"This could mean:")
        print(f"  1. API requires different authentication method")
        print(f"  2. Different base URL needed")
        print(f"  3. Limited API access permissions")
        print(f"  4. API version or path differences")