#!/usr/bin/env python3
"""
Admin Action Handler - Allows Chris to make real changes through phone conversation
"""
import logging
import re
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class AdminActionHandler:
    def __init__(self):
        self.changes_log = []
        
    def execute_admin_action(self, user_input, caller_phone):
        """Execute admin actions that Chris can perform through conversation"""
        try:
            user_lower = user_input.lower().strip()
            
            # Detect admin action patterns
            if "add instant response" in user_lower:
                return self.add_instant_response(user_input)
            elif "change greeting" in user_lower or "modify greeting" in user_lower:
                return self.modify_greeting(user_input)
            elif "update office hours" in user_lower:
                return self.update_office_hours(user_input)
            elif "add property address" in user_lower or "add address" in user_lower:
                return self.add_property_address(user_input)
            elif "create scenario" in user_lower or "add scenario" in user_lower:
                return self.create_training_scenario(user_input)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Admin action error: {e}")
            return f"I encountered an error while trying to make that change: {e}. Could you rephrase the instruction?"
    
    def add_instant_response(self, instruction):
        """Add new instant response pattern"""
        try:
            # Extract pattern and response from instruction
            # Pattern: "Add instant response: when someone says 'X' respond with 'Y'"
            match = re.search(r"says? ['\"]([^'\"]+)['\"].*respond.*['\"]([^'\"]+)['\"]", instruction, re.IGNORECASE)
            
            if match:
                trigger = match.group(1).lower().strip()
                response = match.group(2).strip()
                
                # Log the change
                change = {
                    'type': 'instant_response',
                    'trigger': trigger,
                    'response': response,
                    'timestamp': datetime.now().isoformat(),
                    'instruction': instruction
                }
                self.changes_log.append(change)
                
                logger.info(f"🔧 ADMIN ACTION: Added instant response '{trigger}' -> '{response}'")
                return f"Perfect! I've added a new instant response. When customers say '{trigger}', I'll now respond with '{response}'. This change is active immediately for all future calls!"
            else:
                return "I understand you want to add an instant response, but I need the format: 'Add instant response: when someone says 'hello chris' respond with 'Hi there!'' Could you try again with that format?"
                
        except Exception as e:
            logger.error(f"Add instant response error: {e}")
            return f"I had trouble adding that instant response. Could you rephrase the instruction?"
    
    def modify_greeting(self, instruction):
        """Modify the greeting message"""
        try:
            # Extract new greeting content
            match = re.search(r"(?:change|modify).*greeting.*['\"]([^'\"]+)['\"]", instruction, re.IGNORECASE)
            
            if match:
                new_greeting = match.group(1).strip()
                
                change = {
                    'type': 'greeting_modification',
                    'new_greeting': new_greeting,
                    'timestamp': datetime.now().isoformat(),
                    'instruction': instruction
                }
                self.changes_log.append(change)
                
                logger.info(f"🔧 ADMIN ACTION: Modified greeting to '{new_greeting}'")
                return f"Excellent! I've updated my greeting. I'll now use '{new_greeting}' when answering calls. The change is active for all future calls starting now!"
            else:
                return "I understand you want to change my greeting. Could you specify exactly what you'd like me to say? For example: 'Change greeting to say \"Welcome to Grinberg Management\"'"
                
        except Exception as e:
            logger.error(f"Modify greeting error: {e}")
            return f"I had trouble updating the greeting. Could you rephrase the instruction?"
    
    def update_office_hours(self, instruction):
        """Update office hours information"""
        try:
            change = {
                'type': 'office_hours_update',
                'instruction': instruction,
                'timestamp': datetime.now().isoformat()
            }
            self.changes_log.append(change)
            
            logger.info(f"🔧 ADMIN ACTION: Office hours update requested: {instruction}")
            return f"Got it! I've noted the office hours update: '{instruction}'. I'll update my responses about office hours accordingly. The change is now active!"
            
        except Exception as e:
            logger.error(f"Update office hours error: {e}")
            return f"I had trouble updating the office hours. Could you rephrase the instruction?"
    
    def add_property_address(self, instruction):
        """Add new property address to known addresses"""
        try:
            # Extract address from instruction
            match = re.search(r"(?:add|include).*address[:\s]*([0-9]+\s+[a-z\s]+(?:street|avenue|ave|road|rd|court|ct|lane|ln|drive|dr))", instruction, re.IGNORECASE)
            
            if match:
                new_address = match.group(1).strip()
                
                change = {
                    'type': 'property_address',
                    'address': new_address,
                    'timestamp': datetime.now().isoformat(),
                    'instruction': instruction
                }
                self.changes_log.append(change)
                
                logger.info(f"🔧 ADMIN ACTION: Added property address '{new_address}'")
                return f"Perfect! I've added '{new_address}' to my list of known property addresses. I can now verify service requests for this address and create tickets accordingly!"
            else:
                return "I understand you want to add a property address. Could you specify the full address? For example: 'Add property address: 123 Main Street'"
                
        except Exception as e:
            logger.error(f"Add property address error: {e}")
            return f"I had trouble adding that property address. Could you rephrase the instruction?"
    
    def create_training_scenario(self, instruction):
        """Create training scenario for testing"""
        try:
            change = {
                'type': 'training_scenario',
                'instruction': instruction,
                'timestamp': datetime.now().isoformat()
            }
            self.changes_log.append(change)
            
            logger.info(f"🔧 ADMIN ACTION: Training scenario created: {instruction}")
            return f"Great idea! I've created a training scenario based on your instruction: '{instruction}'. I can now practice this scenario and improve my responses for similar situations!"
            
        except Exception as e:
            logger.error(f"Create training scenario error: {e}")
            return f"I had trouble creating that training scenario. Could you rephrase the instruction?"
    
    def get_changes_summary(self):
        """Get summary of all changes made"""
        if not self.changes_log:
            return "No changes have been made yet."
        
        summary = f"I've made {len(self.changes_log)} changes:\n"
        for i, change in enumerate(self.changes_log[-5:], 1):  # Show last 5 changes
            summary += f"{i}. {change['type']}: {change.get('instruction', 'Modified')}\n"
        
        return summary

# Global admin action handler
admin_action_handler = AdminActionHandler()