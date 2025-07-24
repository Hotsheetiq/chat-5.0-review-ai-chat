#!/usr/bin/env python3
"""
Check the /Help endpoint to get API documentation
"""

import asyncio
import aiohttp
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_api_help():
    """Check the Help endpoint for API documentation"""
    
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
            
            # Check the Help endpoint
            logger.info(f"🔍 Checking /Help endpoint...")
            async with session.get(f"{base_url}/Help", headers=headers) as resp:
                if resp.status == 200:
                    help_content = await resp.text()
                    logger.info(f"📄 Help content length: {len(help_content)}")
                    
                    # Save to file and show relevant parts
                    with open("rent_manager_help.html", "w") as f:
                        f.write(help_content)
                    
                    # Look for API endpoints in the help content
                    lines = help_content.split('\n')
                    api_lines = []
                    for line in lines:
                        if any(keyword in line.lower() for keyword in ['api', 'endpoint', 'service', 'work', 'maintenance', 'request']):
                            api_lines.append(line.strip())
                    
                    logger.info(f"📋 Found {len(api_lines)} relevant lines:")
                    for line in api_lines[:20]:  # Show first 20 relevant lines
                        if line:
                            logger.info(f"   {line}")
            
            # Check the Help/Resources endpoint
            logger.info(f"🔍 Checking /Help/Resources endpoint...")
            async with session.get(f"{base_url}/Help/Resources", headers=headers) as resp:
                if resp.status == 200:
                    resources_content = await resp.text()
                    logger.info(f"📄 Resources content length: {len(resources_content)}")
                    
                    with open("rent_manager_resources.html", "w") as f:
                        f.write(resources_content)
            
            # Try a different authentication approach - maybe we need to use different headers
            logger.info(f"🔧 Testing different authentication headers...")
            
            alt_headers = [
                {"Authorization": f"Bearer {token}"},
                {"X-API-Token": token},
                {"API-Token": token},
                {"Token": token},
                {"SessionToken": token},
                {"RentManager-Token": token}
            ]
            
            for i, alt_header in enumerate(alt_headers):
                alt_header.update({"Content-Type": "application/json", "Accept": "application/json"})
                
                async with session.get(f"{base_url}/Tenants", headers=alt_header) as resp:
                    logger.info(f"🔑 Alt header {i+1} (/Tenants): {resp.status}")
                    if resp.status == 200:
                        logger.info(f"✅ SUCCESS with header: {alt_header}")
                        return alt_header
                    
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_api_help())