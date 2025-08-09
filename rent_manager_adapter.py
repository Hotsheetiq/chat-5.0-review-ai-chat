"""
Rent Manager Truth Gate - Production Adapter
Provides verify_property and create_ticket functions for the production system
"""

import logging
import os
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

def verify_property(address: str) -> Optional[Dict[str, Any]]:
    """
    Verify property address against Rent Manager
    Returns property data if found, None if not found
    """
    try:
        # Import existing property backup system
        from comprehensive_property_data import address_matcher
        
        # Use address matcher for property verification
        matched_properties = address_matcher.find_matching_properties(address)
        
        if matched_properties:
            # Return first match with Rent Manager format
            prop = matched_properties[0]
            return {
                'propertyId': prop.get('PropertyID'),
                'name': prop.get('Name', ''),
                'address': prop.get('StreetAddress', ''),
                'city': prop.get('City', ''),
                'state': prop.get('State', ''),
                'zipCode': prop.get('PostalCode', ''),
                'verified': True
            }
        
        logger.warning(f"Property not found in backup system: {address}")
        return None
        
    except Exception as e:
        logger.error(f"Property verification failed: {e}")
        return None

def create_ticket(property_id: str, ticket_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create service ticket in Rent Manager
    Returns ticket data with ticketId if successful, None if failed
    """
    try:
        # Import existing rent manager client
        from rent_manager import rent_manager_client
        
        # Format ticket data for Rent Manager API
        rm_ticket_data = {
            "PropertyID": property_id,
            "Description": ticket_data.get('description', ''),
            "Priority": ticket_data.get('priority', 'Standard'),
            "Category": ticket_data.get('category', 'Maintenance'),
            "ContactName": ticket_data.get('contact_name', ''),
            "ContactPhone": ticket_data.get('contact_phone', ''),
            "UnitNumber": ticket_data.get('unit_number', ''),
            "Issue": ticket_data.get('issue', ''),
            "AccessInstructions": ticket_data.get('access_instructions', '')
        }
        
        # Attempt to create ticket via Rent Manager API
        result = rent_manager_client.create_service_issue(rm_ticket_data)
        
        if result and result.get('ServiceIssueID'):
            logger.info(f"✅ Ticket created: {result['ServiceIssueID']}")
            return {
                'ticketId': result['ServiceIssueID'],
                'success': True,
                'message': f"Ticket {result['ServiceIssueID']} created successfully"
            }
        
        logger.warning("Rent Manager API did not return a ticket ID")
        return None
        
    except Exception as e:
        logger.error(f"Ticket creation failed: {e}")
        return None

def suggest_similar_properties(partial_address: str, limit: int = 3) -> list:
    """
    Suggest similar property addresses for spelling assistance
    """
    try:
        from comprehensive_property_data import address_matcher
        
        # Use fuzzy matching to find similar addresses
        suggestions = address_matcher.get_address_suggestions(partial_address, limit)
        
        return [
            {
                'address': prop.get('StreetAddress', ''),
                'city': prop.get('City', ''),
                'propertyId': prop.get('PropertyID'),
                'confidence': prop.get('match_confidence', 0.0)
            }
            for prop in suggestions
        ]
        
    except Exception as e:
        logger.error(f"Address suggestion failed: {e}")
        return []

def format_property_confirmation(property_data: Dict[str, Any]) -> str:
    """
    Format property data for voice confirmation
    """
    if not property_data:
        return "I couldn't find that property in our system."
    
    address = property_data.get('address', '')
    city = property_data.get('city', '')
    
    if address and city:
        return f"I found the property at {address}, {city}."
    elif address:
        return f"I found the property at {address}."
    else:
        return "I found a matching property in our system."

# Emergency keywords for priority classification
EMERGENCY_KEYWORDS = {
    'no heat', 'heat not working', 'no heating',
    'flooding', 'flood', 'water flooding',
    'clogged toilet', 'toilet clogged', 'sewer backup', 'sewer blocked'
}

def classify_emergency(issue_text: str) -> str:
    """
    Classify issue priority based on emergency keywords
    """
    issue_lower = issue_text.lower()
    
    if any(keyword in issue_lower for keyword in EMERGENCY_KEYWORDS):
        return 'Emergency'
    elif any(keyword in issue_lower for keyword in ['urgent', 'emergency', 'immediate']):
        return 'Urgent'
    else:
        return 'Standard'

def should_create_emergency_ticket(issue_text: str, office_hours: bool) -> bool:
    """
    Determine if emergency ticket should be created immediately
    """
    priority = classify_emergency(issue_text)
    
    # Always create emergency tickets immediately
    if priority == 'Emergency':
        return True
    
    # Create urgent tickets during office hours
    if priority == 'Urgent' and office_hours:
        return True
    
    # Standard tickets wait for office hours
    return False

# Export the main functions
__all__ = [
    'verify_property',
    'create_ticket', 
    'suggest_similar_properties',
    'format_property_confirmation',
    'classify_emergency',
    'should_create_emergency_ticket'
]