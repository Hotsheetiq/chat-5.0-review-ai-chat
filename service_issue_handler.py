import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ServiceIssueHandler:
    """Handles service issue creation with proper confirmation and issue numbers"""
    
    def __init__(self, rent_manager):
        self.rent_manager = rent_manager
    
    async def create_maintenance_issue(self, tenant_info: Dict, issue_type: str, description: str, unit_address: str = None) -> Dict[str, Any]:
        """
        Create a maintenance issue in Rent Manager assigned to Dimitry
        Returns confirmation with issue number
        """
        try:
            # Determine priority based on issue type
            priority = "High" if any(word in issue_type.lower() for word in [
                'emergency', 'urgent', 'electrical', 'gas', 'water', 'power', 'heat', 'flooding'
            ]) else "Normal"
            
            # Build issue data
            issue_data = {
                'tenant_id': tenant_info.get('TenantID') or tenant_info.get('id'),
                'description': f"{issue_type}: {description}",
                'category': self._get_issue_category(issue_type),
                'priority': priority,
                'source': 'voice_assistant',
                'unit': unit_address or tenant_info.get('Unit', ''),
                'notes': f"Reported by {tenant_info.get('Name', 'Phone Caller')} via Chris AI Assistant"
            }
            
            # Create the service issue in Rent Manager
            result = await self.rent_manager.create_service_issue(issue_data)
            
            if result and result.get('success'):
                logger.info(f"Created service issue {result['issue_number']} assigned to Dimitry")
                
                # Return confirmation details
                return {
                    'success': True,
                    'issue_number': result['issue_number'],
                    'issue_id': result['issue_id'],
                    'description': description,
                    'priority': priority,
                    'assigned_to': 'Dimitry Simanovsky',
                    'confirmation_message': f"Perfect! I've created service issue #{result['issue_number']} for your {issue_type.lower()} at {unit_address or tenant_info.get('Unit', 'your unit')}. This has been assigned to Dimitry Simanovsky who will contact you within 2-4 hours."
                }
            else:
                logger.error("Failed to create service issue in Rent Manager")
                return {
                    'success': False,
                    'error': 'Unable to create service issue',
                    'fallback_message': f"I understand you have a {issue_type.lower()} issue at {unit_address or 'your unit'}. I'll make sure our maintenance team contacts you within 2-4 hours to resolve this."
                }
                
        except Exception as e:
            logger.error(f"Service issue creation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_message': f"I've noted your {issue_type.lower()} issue and our maintenance team will contact you within 2-4 hours."
            }
    
    def _get_issue_category(self, issue_type: str) -> str:
        """Determine issue category based on type"""
        issue_lower = issue_type.lower()
        
        if any(word in issue_lower for word in ['electrical', 'power', 'electricity', 'lights']):
            return 'Electrical'
        elif any(word in issue_lower for word in ['plumbing', 'water', 'leak', 'flooding', 'drain']):
            return 'Plumbing'
        elif any(word in issue_lower for word in ['heating', 'heat', 'hvac', 'air', 'temperature']):
            return 'HVAC'
        elif any(word in issue_lower for word in ['gas', 'appliance']):
            return 'Appliance'
        elif any(word in issue_lower for word in ['door', 'window', 'lock', 'key']):
            return 'Security'
        else:
            return 'General Maintenance'
    
    async def create_general_task(self, caller_phone: str, description: str, category: str = 'general') -> Dict[str, Any]:
        """
        Create a general task for office follow-up
        Returns confirmation with task number
        """
        try:
            task_data = {
                'description': description,
                'category': category,
                'priority': 'normal',
                'source': 'voice_assistant',
                'caller_phone': caller_phone
            }
            
            # Create worker task in Rent Manager
            task_id = await self.rent_manager.create_worker_task(task_data)
            
            if task_id:
                return {
                    'success': True,
                    'task_id': task_id,
                    'task_number': f"TASK-{task_id}",
                    'confirmation_message': f"I've created task #{task_id} for our office team. Someone will call you back within 2-4 hours to assist you."
                }
            else:
                return {
                    'success': False,
                    'fallback_message': "I've noted your request and our team will contact you within 2-4 hours."
                }
                
        except Exception as e:
            logger.error(f"Task creation error: {e}")
            return {
                'success': False,
                'error': str(e),
                'fallback_message': "I've made a note of your request and our team will follow up with you."
            }