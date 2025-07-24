import os
import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class RentManagerAPI:
    """
    Rent Manager API integration for tenant management, notes, and service issues.
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://grinb-api.rentmanager.com"  # Your actual Rent Manager API URL
        self.headers = {
            "X-RM12Api-ApiToken": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make an HTTP request to the Rent Manager API."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.request(method, url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 404:
                        return None
                    else:
                        logger.error(f"Rent Manager API error: {response.status} - {await response.text()}")
                        return None
                        
        except aiohttp.ClientError as e:
            logger.error(f"Network error accessing Rent Manager API: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Rent Manager API: {e}")
            return None
    
    async def lookup_tenant_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Look up a tenant by their phone number.
        Returns tenant data if found, None otherwise.
        """
        try:
            # Clean phone number (remove formatting)
            clean_phone = ''.join(filter(str.isdigit, phone_number))
            
            # Search for tenant by phone number
            endpoint = f"/tenants/search?phone={clean_phone}"
            result = await self._make_request("GET", endpoint)
            
            if result and result.get('tenants'):
                tenant = result['tenants'][0]  # Get first match
                logger.info(f"Found tenant: {tenant.get('name', 'Unknown')} for phone {phone_number}")
                return {
                    'id': tenant.get('id'),
                    'name': tenant.get('name'),
                    'phone': tenant.get('phone'),
                    'email': tenant.get('email'),
                    'unit': tenant.get('unit'),
                    'property': tenant.get('property'),
                    'lease_status': tenant.get('lease_status', 'active')
                }
            
            logger.info(f"No tenant found for phone number: {phone_number}")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up tenant by phone {phone_number}: {e}")
            return None
    
    async def add_tenant_note(self, tenant_id: str, note_data: Dict[str, Any]) -> bool:
        """
        Add a note to a tenant's record.
        """
        try:
            endpoint = f"/tenants/{tenant_id}/notes"
            
            note_payload = {
                "note": note_data.get('note', ''),
                "category": note_data.get('type', 'general'),
                "date": note_data.get('timestamp', asyncio.get_event_loop().time()),
                "created_by": "Voice Assistant",
                "is_private": False
            }
            
            result = await self._make_request("POST", endpoint, note_payload)
            
            if result:
                logger.info(f"Successfully added note to tenant {tenant_id}")
                return True
            else:
                logger.error(f"Failed to add note to tenant {tenant_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error adding note to tenant {tenant_id}: {e}")
            return False
    
    async def create_service_issue(self, issue_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a new service/maintenance issue.
        Returns the issue ID if successful, None otherwise.
        """
        try:
            endpoint = "/service-issues"
            
            issue_payload = {
                "tenant_id": issue_data.get('tenant_id'),
                "description": issue_data.get('description', ''),
                "category": issue_data.get('category', 'maintenance'),
                "priority": issue_data.get('priority', 'normal'),
                "status": "open",
                "source": issue_data.get('source', 'voice_assistant'),
                "created_by": "Voice Assistant",
                "date_reported": asyncio.get_event_loop().time()
            }
            
            result = await self._make_request("POST", endpoint, issue_payload)
            
            if result and result.get('issue_id'):
                issue_id = result['issue_id']
                logger.info(f"Successfully created service issue {issue_id} for tenant {issue_data.get('tenant_id')}")
                return issue_id
            else:
                logger.error(f"Failed to create service issue for tenant {issue_data.get('tenant_id')}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating service issue: {e}")
            return None
    
    async def create_worker_task(self, task_data: Dict[str, Any]) -> Optional[str]:
        """
        Create a worker task for staff follow-up.
        Returns the task ID if successful, None otherwise.
        """
        try:
            endpoint = "/worker-tasks"
            
            task_payload = {
                "description": task_data.get('description', ''),
                "category": task_data.get('category', 'general'),
                "priority": task_data.get('priority', 'normal'),
                "status": "pending",
                "assigned_to": None,  # Will be assigned by office staff
                "source": task_data.get('source', 'voice_assistant'),
                "created_by": "Voice Assistant",
                "date_created": asyncio.get_event_loop().time(),
                "caller_phone": task_data.get('caller_phone')
            }
            
            result = await self._make_request("POST", endpoint, task_payload)
            
            if result and result.get('task_id'):
                task_id = result['task_id']
                logger.info(f"Successfully created worker task {task_id} for caller {task_data.get('caller_phone')}")
                return task_id
            else:
                logger.error(f"Failed to create worker task for caller {task_data.get('caller_phone')}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating worker task: {e}")
            return None
    
    async def get_tenant_info(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed tenant information by ID.
        """
        try:
            endpoint = f"/tenants/{tenant_id}"
            result = await self._make_request("GET", endpoint)
            
            if result:
                logger.info(f"Retrieved info for tenant {tenant_id}")
                return result
            else:
                logger.error(f"Failed to retrieve tenant info for {tenant_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting tenant info for {tenant_id}: {e}")
            return None
    
    async def get_property_units(self, property_id: str) -> List[Dict[str, Any]]:
        """
        Get available units for a property.
        """
        try:
            endpoint = f"/properties/{property_id}/units?status=available"
            result = await self._make_request("GET", endpoint)
            
            if result and result.get('units'):
                logger.info(f"Retrieved {len(result['units'])} available units for property {property_id}")
                return result['units']
            else:
                logger.info(f"No available units found for property {property_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting property units for {property_id}: {e}")
            return []
    
    async def update_service_issue(self, issue_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an existing service issue.
        """
        try:
            endpoint = f"/service-issues/{issue_id}"
            result = await self._make_request("PUT", endpoint, update_data)
            
            if result:
                logger.info(f"Successfully updated service issue {issue_id}")
                return True
            else:
                logger.error(f"Failed to update service issue {issue_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating service issue {issue_id}: {e}")
            return False
