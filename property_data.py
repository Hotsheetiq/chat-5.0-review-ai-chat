import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class PropertyDataManager:
    """
    Manages property information and common responses for the voice assistant.
    This provides a knowledge base for general property questions.
    """
    
    def __init__(self):
        # This would typically come from a database or configuration file
        self.property_info = {
            "office_hours": {
                "weekdays": "9:00 AM to 6:00 PM",
                "saturday": "10:00 AM to 4:00 PM", 
                "sunday": "Closed",
                "emergency": "24/7 emergency maintenance available"
            },
            "contact_info": {
                "office_phone": "Main office",
                "emergency_phone": "Emergency maintenance line",
                "email": "leasing@property.com",
                "address": "Property Management Office"
            },
            "amenities": [
                "Swimming pool",
                "Fitness center", 
                "Clubhouse",
                "Business center",
                "Pet-friendly areas",
                "On-site laundry",
                "Covered parking",
                "24-hour maintenance"
            ],
            "policies": {
                "pet_policy": "Pets welcome with deposit and monthly fee. Breed restrictions apply.",
                "parking": "One assigned parking space per unit. Guest parking available.",
                "lease_terms": "6, 9, and 12-month lease terms available",
                "application_fee": "Application processing fee applies",
                "security_deposit": "Security deposit required based on credit score"
            },
            "maintenance": {
                "emergency_types": [
                    "No heat or air conditioning",
                    "Plumbing leaks or blockages", 
                    "Electrical issues",
                    "Lock-outs",
                    "Security concerns"
                ],
                "normal_response": "1-3 business days",
                "urgent_response": "Same day",
                "emergency_response": "Immediate"
            }
        }
        
        self.common_responses = {
            "greeting": "Thank you for calling our property management office. How can I help you today?",
            "maintenance_request": "I'll be happy to help you with your maintenance request. Can you please describe the issue?",
            "leasing_inquiry": "I'd be glad to help you with information about our available units. What type of unit are you looking for?",
            "office_hours": f"Our office hours are {self.property_info['office_hours']['weekdays']} Monday through Friday, and {self.property_info['office_hours']['saturday']} on Saturday. We're closed on Sunday, but emergency maintenance is available 24/7.",
            "application_process": "To apply for a unit, you can visit our office during business hours or apply online. We'll need to run a credit check and verify your income and references.",
            "pet_policy": self.property_info['policies']['pet_policy'],
            "parking_info": self.property_info['policies']['parking']
        }
    
    def get_office_hours(self) -> str:
        """Get office hours information."""
        hours = self.property_info['office_hours']
        return (f"Our office hours are {hours['weekdays']} Monday through Friday, "
                f"{hours['saturday']} on Saturday. We're closed Sunday. "
                f"However, {hours['emergency']}.")
    
    def get_amenities(self) -> List[str]:
        """Get list of property amenities."""
        return self.property_info['amenities']
    
    def get_amenities_text(self) -> str:
        """Get amenities as formatted text."""
        amenities = self.get_amenities()
        if len(amenities) <= 3:
            return ", ".join(amenities)
        else:
            return ", ".join(amenities[:-1]) + f", and {amenities[-1]}"
    
    def get_maintenance_info(self, issue_type: str = "general") -> Dict[str, str]:
        """Get maintenance response time information."""
        maintenance = self.property_info['maintenance']
        
        if any(emergency in issue_type.lower() 
               for emergency in ["emergency", "urgent", "leak", "heat", "air", "electrical"]):
            return {
                "response_time": maintenance['emergency_response'],
                "priority": "emergency"
            }
        elif any(urgent in issue_type.lower() 
                for urgent in ["broken", "not working", "urgent"]):
            return {
                "response_time": maintenance['urgent_response'], 
                "priority": "urgent"
            }
        else:
            return {
                "response_time": maintenance['normal_response'],
                "priority": "normal"
            }
    
    def get_contact_info(self) -> Dict[str, str]:
        """Get contact information."""
        return self.property_info['contact_info']
    
    def get_policy_info(self, policy_type: str) -> Optional[str]:
        """Get information about a specific policy."""
        return self.property_info['policies'].get(policy_type)
    
    def get_common_response(self, response_type: str) -> Optional[str]:
        """Get a common response template."""
        return self.common_responses.get(response_type)
    
    def categorize_inquiry(self, inquiry_text: str) -> str:
        """
        Categorize the type of inquiry based on keywords.
        Returns: maintenance, leasing, general, emergency
        """
        inquiry_lower = inquiry_text.lower()
        
        # Emergency keywords
        emergency_keywords = ["emergency", "urgent", "broken", "leak", "flooding", "no heat", "no air", "electrical"]
        if any(keyword in inquiry_lower for keyword in emergency_keywords):
            return "emergency"
        
        # Maintenance keywords
        maintenance_keywords = ["fix", "repair", "maintenance", "broken", "not working", "issue", "problem"]
        if any(keyword in inquiry_lower for keyword in maintenance_keywords):
            return "maintenance"
        
        # Leasing keywords
        leasing_keywords = ["lease", "rent", "available", "unit", "apartment", "apply", "application", "tour", "move in"]
        if any(keyword in inquiry_lower for keyword in leasing_keywords):
            return "leasing"
        
        return "general"
    
    def get_suggested_response(self, inquiry_type: str, context: str = "") -> str:
        """
        Get a suggested response based on inquiry type and context.
        """
        if inquiry_type == "emergency":
            return ("I understand this is an emergency situation. I'm creating a high-priority "
                   "service request right now. Our emergency maintenance team will respond immediately. "
                   "If this is a life-threatening emergency, please hang up and call 911.")
        
        elif inquiry_type == "maintenance":
            return ("I'll help you with your maintenance request. I'm gathering the details and "
                   "will create a service request for you. Our maintenance team typically responds "
                   "within 1-3 business days for standard requests.")
        
        elif inquiry_type == "leasing":
            return ("I'd be happy to help you with leasing information. Let me gather your contact "
                   "details and preferences so our leasing team can follow up with you about "
                   "available units and schedule a tour.")
        
        else:
            return ("Thank you for your call. I'm here to help with any questions about our "
                   "property, maintenance requests, or leasing information. How can I assist you today?")
    
    def format_unit_info(self, unit_data: Dict[str, Any]) -> str:
        """Format unit information for voice response."""
        try:
            unit_type = unit_data.get('type', 'unit')
            bedrooms = unit_data.get('bedrooms', 'studio')
            bathrooms = unit_data.get('bathrooms', '1')
            rent = unit_data.get('rent', 'market rate')
            available_date = unit_data.get('available_date', 'immediately')
            
            return (f"We have a {bedrooms} bedroom, {bathrooms} bathroom {unit_type} "
                   f"available {available_date} for {rent} per month.")
                   
        except Exception as e:
            logger.error(f"Error formatting unit info: {e}")
            return "We have units available. Please contact our office for specific details."
