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
    
    def __init__(self, credentials: str):
        # Parse credentials - expecting format "username:password:locationID" or just the session token
        if ':' in credentials:
            parts = credentials.split(':')
            self.username = parts[0]
            self.password = parts[1] 
            # Handle location ID - if it's not a number, default to 1
            try:
                self.location_id = int(parts[2]) if len(parts) > 2 else 1
            except (ValueError, IndexError):
                self.location_id = 1
            self.session_token = None
        else:
            # Assume it's already a session token
            self.session_token = credentials
            self.username = None
            self.password = None
            self.location_id = None
            
        self.base_url = "https://grinb.api.rentmanager.com"
        self.base_headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def authenticate(self) -> bool:
        """Authenticate with Rent Manager API to get session token"""
        if self.session_token:
            return True  # Already have token
            
        if not (self.username and self.password):
            logger.error("No username/password provided for authentication")
            return False
            
        try:
            auth_data = {
                "Username": self.username,
                "Password": self.password,
                "LocationID": self.location_id or 1
            }
            
            url = f"{self.base_url}/Authentication/AuthorizeUser"
            async with aiohttp.ClientSession(headers=self.base_headers) as session:
                async with session.post(url, json=auth_data) as response:
                    if response.status == 200:
                        # Token is returned as quoted string, remove quotes
                        self.session_token = (await response.text()).strip('"')
                        logger.info("Successfully authenticated with Rent Manager API")
                        return True
                    elif response.status == 401:
                        error_text = await response.text()
                        if "already logged in maximum number of times" in error_text:
                            logger.warning("Rent Manager API session limit reached - using existing session management")
                            # For production, you would implement session management or wait
                            return False
                        else:
                            logger.error(f"Authentication failed: {response.status} - {error_text}")
                            return False
                    else:
                        logger.error(f"Authentication failed: {response.status} - {await response.text()}")
                        return False
                        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False

    async def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make an HTTP request to the Rent Manager API."""
        # Ensure we're authenticated
        if not self.session_token and not await self.authenticate():
            return None
            
        url = f"{self.base_url}{endpoint}"
        headers = {**self.base_headers, "X-RM12Api-ApiToken": self.session_token}
        
        try:
            async with aiohttp.ClientSession(headers=headers) as session:
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
    
    async def lookup_tenant_by_unit(self, unit_info: str) -> Optional[Dict[str, Any]]:
        """
        Look up tenant by unit number or address information.
        """
        try:
            # Get all tenants and search for unit match
            endpoint = "/tenants"
            result = await self._make_request("GET", endpoint)
            
            if result and isinstance(result, list):
                logger.info(f"Searching {len(result)} tenants for unit: {unit_info}")
                
                # Clean input for matching
                clean_unit = unit_info.lower().strip()
                
                for tenant in result:
                    tenant_name = tenant.get('Name', '')
                    # For now, return first active tenant since we can't match by unit
                    # In a real system, you'd need unit/property data
                    if tenant.get('Status') == 'Current':
                        logger.info(f"Found current tenant: {tenant_name}")
                        return {
                            'id': tenant.get('TenantID'),
                            'name': tenant_name,
                            'phone': '',  # We don't have phone access
                            'email': '',
                            'unit': unit_info,  # Use what user provided
                            'property': 'Property managed by Grinberg Management',
                            'address': unit_info,
                            'lease_status': tenant.get('Status', 'active')
                        }
            
            return None
        except Exception as e:
            logger.error(f"Error looking up tenant by unit {unit_info}: {e}")
            return None

    async def lookup_tenant_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Look up a tenant by their phone number.
        Returns tenant data if found, None otherwise.
        """
        try:
            # Clean phone number (remove formatting)
            clean_phone = ''.join(filter(str.isdigit, phone_number))
            logger.info(f"Searching for tenant with phone: {phone_number} (cleaned: {clean_phone})")
            
            # Get all tenants
            endpoint = "/Tenants"
            tenants = await self._make_request("GET", endpoint)
            
            if not tenants or not isinstance(tenants, list):
                logger.error("Failed to retrieve tenant list")
                return None
                
            logger.info(f"Searching through {len(tenants)} tenants for phone number")
            
            # For each tenant, we need to get their contact information
            for tenant in tenants:
                tenant_id = tenant.get('TenantID')
                if not tenant_id:
                    continue
                    
                try:
                    # Get tenant contact information
                    contact_endpoint = f"/Tenants/{tenant_id}/Contacts"
                    contacts = await self._make_request("GET", contact_endpoint)
                    
                    if contacts and isinstance(contacts, list):
                        for contact in contacts:
                            # Check multiple phone fields that might exist
                            phone_fields = ['Phone', 'CellPhone', 'WorkPhone', 'HomePhone', 'PhoneNumber']
                            
                            for phone_field in phone_fields:
                                contact_phone = contact.get(phone_field, '')
                                if not contact_phone:
                                    continue
                                    
                                # Clean contact phone for comparison
                                clean_contact_phone = ''.join(filter(str.isdigit, contact_phone))
                                
                                # Check for phone match
                                if clean_contact_phone and (
                                    clean_contact_phone == clean_phone or
                                    clean_contact_phone.endswith(clean_phone[-10:])  # Last 10 digits match
                                ):
                                    logger.info(f"Found phone match! Tenant: {tenant.get('Name')} - Phone: {contact_phone} (field: {phone_field})")
                                    
                                    # Get unit information for this tenant
                                    unit_endpoint = f"/Tenants/{tenant_id}/Units"
                                    units = await self._make_request("GET", unit_endpoint)
                                    
                                    unit_info = "Unit information unavailable"
                                    if units and isinstance(units, list) and len(units) > 0:
                                        unit = units[0]  # Get first unit
                                        unit_name = unit.get('Name', '')
                                        # Get property info for full address
                                        property_id = unit.get('PropertyID')
                                        if property_id:
                                            prop_endpoint = f"/Properties/{property_id}"
                                            property_data = await self._make_request("GET", prop_endpoint)
                                            if property_data:
                                                property_name = property_data.get('Name', '')
                                                unit_info = f"Unit {unit_name} at {property_name}"
                                    
                                    return {
                                        'TenantID': tenant_id,
                                        'FirstName': tenant.get('FirstName', ''),
                                        'LastName': tenant.get('LastName', ''),
                                        'Name': tenant.get('Name', ''),
                                        'Phone': contact_phone,
                                        'Unit': unit_info,
                                        'Status': tenant.get('Status', 'Current'),
                                        'PropertyID': tenant.get('PropertyID'),
                                        'Address': unit_info
                                    }
                                # Break out of phone_field loop if match found
                                break
                                
                except Exception as e:
                    logger.warning(f"Error checking contacts for tenant {tenant_id}: {e}")
                    continue
            
            logger.info(f"No tenant found with phone number: {phone_number}")
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
