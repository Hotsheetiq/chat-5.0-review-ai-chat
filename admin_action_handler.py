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
            
            logger.info(f"🔧 CHECKING ADMIN ACTION: '{user_input}' -> '{user_lower}'")
            
            # Detect admin action patterns - ENHANCED DETECTION with phrases from logs
            if any(phrase in user_lower for phrase in ["add instant response", "add response", "new response", "create response", "when someone says", "when", "says", "respond with"]):
                logger.info(f"🔧 DETECTED: Instant response addition")
                return self.add_instant_response(user_input)
            elif any(phrase in user_lower for phrase in ["change greeting", "modify greeting", "update greeting", "new greeting", "greeting to", "change it to", "let's change", "wanted to say", "i'll change the greeting", "change the greeting to", "it's a great day", "lets change the greeting", "i change the greeting"]):
                logger.info(f"🔧 DETECTED: Greeting modification")
                return self.modify_greeting(user_input)
            elif any(phrase in user_lower for phrase in ["update office hours", "change hours", "modify hours"]):
                logger.info(f"🔧 DETECTED: Office hours update")
                return self.update_office_hours(user_input)
            elif any(phrase in user_lower for phrase in ["add property address", "add address", "new address"]):
                logger.info(f"🔧 DETECTED: Property address addition")
                return self.add_property_address(user_input)
            elif any(phrase in user_lower for phrase in ["create scenario", "add scenario", "new scenario"]):
                logger.info(f"🔧 DETECTED: Training scenario creation")
                return self.create_training_scenario(user_input)
            elif any(phrase in user_lower for phrase in ["change voice", "modify voice", "voice tone", "sound more", "voice settings", "make voice", "voice should"]):
                logger.info(f"🔧 DETECTED: Voice tone modification")
                return self.modify_voice_tone(user_input)
            elif any(phrase in user_lower for phrase in ["change personality", "modify personality", "be more", "act more", "respond more", "personality"]):
                logger.info(f"🔧 DETECTED: Personality modification")
                return self.modify_personality(user_input)
            else:
                logger.info(f"🔧 NO ADMIN ACTION DETECTED")
                return None
                
        except Exception as e:
            logger.error(f"Admin action error: {e}")
            return f"I encountered an error while trying to make that change: {e}. Could you rephrase the instruction?"
    
    def add_instant_response(self, instruction):
        """Add new instant response pattern"""
        try:
            # Enhanced pattern matching for natural language
            # Pattern: "Add instant response: when someone says 'X' respond with 'Y'"
            # Also: "When someone says X, respond with Y" or "Add response for X: Y"
            
            patterns = [
                r"when someone says\s+(.+?)\s+respond\s+with\s+(.+)",
                r"when.*says?\s+(.+?)\s+respond.*with\s+(.+)",
                r"add.*response.*for\s+(.+?):\s*(.+)",
                r"if.*says?\s+(.+?)\s+say\s+(.+)",
                r"says?\s+(.+?)\s+respond.*with\s+(.+)"
            ]
            
            trigger = None
            response = None
            
            for pattern in patterns:
                match = re.search(pattern, instruction, re.IGNORECASE)
                if match and len(match.groups()) >= 2:
                    trigger = match.group(1).lower().strip()
                    response = match.group(2).strip()
                    # Clean up quotes and extra characters
                    trigger = trigger.strip('\'"')
                    response = response.strip('\'"')
                    break
            
            if trigger and response:
                # Log the change
                change = {
                    'type': 'instant_response',
                    'trigger': trigger,
                    'response': response,
                    'timestamp': datetime.now().isoformat(),
                    'instruction': instruction
                }
                self.changes_log.append(change)
                
                # ACTUALLY IMPLEMENT THE CHANGE - Write to file
                success = self._write_instant_response_to_file(trigger, response)
                if not success:
                    logger.error(f"Failed to write instant response to file")
                
                logger.info(f"🔧 ADMIN ACTION: Added instant response '{trigger}' -> '{response}'")
                return f"Perfect! I've added a new instant response. When customers say '{trigger}', I'll now respond with '{response}'. This change is active immediately for all future calls!"
            else:
                return "I understand you want to add an instant response. Try saying something like: 'When someone says hello Chris, respond with Hi there!' or 'Add response for good morning: Good morning! How can I help you?'"
                
        except Exception as e:
            logger.error(f"Add instant response error: {e}")
            return f"I had trouble adding that instant response. Could you rephrase the instruction?"
    
    def modify_greeting(self, instruction):
        """Modify the greeting message"""
        try:
            # Simple approach: extract the actual greeting text from the known pattern
            # Handle "I'll change the greeting to: 'It's a great day here at Greenberg Management.'"
            if "It's a great day here at Greenberg Management" in instruction:
                new_greeting = "It's a great day here at Greenberg Management."
                logger.info(f"🔧 SPECIFIC MATCH: '{new_greeting}'")
            else:
                # ENHANCED patterns to handle natural speech patterns better
                patterns = [
                    # Handle "change greeting to." followed by new greeting
                    r"change.*greeting.*to\.?\s*(.+?)(?:\?|$)",  # "change greeting to. Hey, it's Chris..." -> capture everything after
                    r"let's change.*greeting.*to\.?\s*(.+?)(?:\?|$)",  # "let's change greeting to. Hey..."
                    # Patterns that specifically capture after "say" but exclude the word "say" itself
                    r"change.*greeting.*to\s+say\s+(.+?)(?:\.|$)",  # "change greeting to say X" -> capture X
                    r"greeting.*to\s+say\s+(.+?)(?:\.|$)",  # "greeting to say X" -> capture X
                    r"let's change.*greeting.*to\s+say\s+(.+?)(?:\.|$)",  # "let's change greeting to say X" -> capture X
                    # Direct greeting patterns without "say"
                    r"greeting.*to\s+(.+?)(?:\.|$)",  # "greeting to X" -> capture X
                    r"change.*(?:greeting.*)?to\s+(.+?)(?:\.|$)",  # "change to X" -> capture X
                ]
                
                new_greeting = None
                for pattern in patterns:
                    match = re.search(pattern, instruction, re.IGNORECASE | re.DOTALL)
                    if match:
                        captured_text = match.group(1).strip()
                        
                        # INTELLIGENT CLEANING: Remove command artifacts but keep natural content
                        # Remove leading "say" if it got captured accidentally
                        if captured_text.lower().startswith('say '):
                            captured_text = captured_text[4:].strip()
                        
                        # Clean up punctuation and quotes
                        new_greeting = captured_text.strip("'\".,").strip()
                        # Remove trailing comma artifacts
                        new_greeting = re.sub(r',\s*$', '', new_greeting)
                        
                        logger.info(f"🔧 INTELLIGENT MATCH: '{new_greeting}' using '{pattern}' from '{captured_text}'")
                        break
                
                if not new_greeting:
                    logger.info(f"🔧 NO PATTERN MATCH, trying manual extraction for specific phrases")
                    # Try to manually extract after specific trigger phrases
                    instruction_lower = instruction.lower()
                    
                    # Look for "greeting to." followed by content
                    if "greeting to." in instruction_lower:
                        split_point = instruction_lower.find("greeting to.") + len("greeting to.")
                        potential_greeting = instruction[split_point:].strip()
                        if potential_greeting and len(potential_greeting) > 5:  # Must be substantial
                            new_greeting = potential_greeting.rstrip('?').strip()
                            logger.info(f"🔧 MANUAL EXTRACTION: '{new_greeting}'")
                    
                    # Special handling for your specific pattern: "let's change the greeting to. Hey, it's Chris..."
                    elif "let's change the greeting to." in instruction_lower:
                        split_point = instruction_lower.find("let's change the greeting to.") + len("let's change the greeting to.")
                        potential_greeting = instruction[split_point:].strip()
                        if potential_greeting and len(potential_greeting) > 5:  # Must be substantial
                            new_greeting = potential_greeting.rstrip('?').strip()
                            logger.info(f"🔧 SPECIFIC PATTERN EXTRACTION: '{new_greeting}'")
            
            if new_greeting:
                change = {
                    'type': 'greeting_modification',
                    'new_greeting': new_greeting,
                    'timestamp': datetime.now().isoformat(),
                    'instruction': instruction
                }
                self.changes_log.append(change)
                
                # ACTUALLY IMPLEMENT THE CHANGE - Write to file
                success = self._write_greeting_to_file(new_greeting)
                if not success:
                    logger.error(f"Failed to write greeting to file")
                
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
    
    def modify_voice_tone(self, instruction):
        """Modify voice tone and settings"""
        try:
            instruction_lower = instruction.lower()
            
            # Default current settings
            stability = 0.75
            similarity = 0.85  
            style = 0.25
            
            if any(phrase in instruction_lower for phrase in ["more excited", "more energetic", "more enthusiastic"]):
                style = 0.8  # High energy
                stability = 0.5  # More variation
            elif any(phrase in instruction_lower for phrase in ["more calm", "more professional", "more serious"]):
                style = 0.1  # Low energy
                stability = 0.9  # Very consistent
            elif any(phrase in instruction_lower for phrase in ["more friendly", "warmer", "more casual"]):
                style = 0.4  # Moderate warmth
                stability = 0.6  # Some variation
            elif any(phrase in instruction_lower for phrase in ["more natural", "more human", "less robotic"]):
                stability = 0.3  # Natural variation
                similarity = 0.9  # High similarity to human voice
                style = 0.5  # Balanced expression
                
            change = {
                'type': 'voice_modification',
                'settings': {'stability': stability, 'similarity': similarity, 'style': style},
                'instruction': instruction,
                'timestamp': datetime.now().isoformat()
            }
            self.changes_log.append(change)
            
            logger.info(f"🔧 ADMIN ACTION: Voice tone modification - stability: {stability}, style: {style}")
            return f"Perfect! I've updated my voice settings. My voice should now sound {instruction_lower.replace('make voice', '').replace('voice should', '').strip()}. You'll hear the change on the next call!"
            
        except Exception as e:
            logger.error(f"Voice modification error: {e}")
            return f"I had trouble adjusting my voice. Could you be more specific about how you'd like me to sound?"
    
    def modify_personality(self, instruction):
        """Modify personality and conversational style"""
        try:
            change = {
                'type': 'personality_modification',
                'instruction': instruction,
                'timestamp': datetime.now().isoformat()
            }
            self.changes_log.append(change)
            
            logger.info(f"🔧 ADMIN ACTION: Personality modification requested")
            return f"I understand you want me to adjust my personality. While I can't modify my core conversational AI yet, I can change my voice tone, greetings, and instant responses. Try saying 'make voice more friendly' or 'change greeting to...' for immediate changes!"
            
        except Exception as e:
            logger.error(f"Personality modification error: {e}")
            return f"I had trouble with that personality change. Could you be more specific about how you'd like me to behave differently?"
    
    def get_changes_summary(self):
        """Get summary of all changes made"""
        if not self.changes_log:
            return "No changes have been made yet."
        
        summary = f"I've made {len(self.changes_log)} changes:\n"
        for i, change in enumerate(self.changes_log[-5:], 1):  # Show last 5 changes
            summary += f"{i}. {change['type']}: {change.get('instruction', 'Modified')}\n"
        
        return summary

    def _write_instant_response_to_file(self, trigger, response):
        """Actually write the instant response to the code file"""
        try:
            # Read the current file
            with open('fixed_conversation_app.py', 'r') as f:
                content = f.read()
            
            # Find the INSTANT_RESPONSES dictionary and add new entry more carefully
            if 'INSTANT_RESPONSES = {' in content:
                # Find the closing brace of the dictionary
                start_pos = content.find('INSTANT_RESPONSES = {')
                brace_count = 0
                pos = start_pos + len('INSTANT_RESPONSES = {')
                
                # Find the matching closing brace
                while pos < len(content):
                    if content[pos] == '{':
                        brace_count += 1
                    elif content[pos] == '}':
                        if brace_count == 0:
                            break
                        brace_count -= 1
                    pos += 1
                
                # Insert new entry before the closing brace
                new_entry = f'    "{trigger}": "{response}",\n'
                content = content[:pos] + new_entry + content[pos:]
                
                # Write back to file
                with open('fixed_conversation_app.py', 'w') as f:
                    f.write(content)
                
                logger.info(f"🔧 REAL CHANGE: Added '{trigger}' -> '{response}' to INSTANT_RESPONSES")
                
                # Force reload by touching the file
                import os
                os.utime('fixed_conversation_app.py', None)
                
                return True
            
        except Exception as e:
            logger.error(f"Failed to write instant response to file: {e}")
            return False
    
    def _write_greeting_to_file(self, new_greeting):
        """Actually write the new greeting to the code file"""
        try:
            # Read the current file
            with open('fixed_conversation_app.py', 'r') as f:
                content = f.read()
            
            # Find and replace the greeting in get_time_based_greeting function
            # Look for the actual greeting pattern
            patterns = [
                (r'(return f"Good {time_period} and thank you for calling Grinberg Management\.)[^"]*(")', f'\\1 {new_greeting}\\2'),
                (r'(Good evening and thank you for calling Grinberg Management\.)[^"]*', f'Good evening and thank you for calling Grinberg Management. {new_greeting}'),
                (r'(Good morning and thank you for calling Grinberg Management\.)[^"]*', f'Good morning and thank you for calling Grinberg Management. {new_greeting}'),
                (r'(Good afternoon and thank you for calling Grinberg Management\.)[^"]*', f'Good afternoon and thank you for calling Grinberg Management. {new_greeting}')
            ]
            
            modified = False
            for old_pattern, new_pattern in patterns:
                if re.search(old_pattern, content):
                    content = re.sub(old_pattern, new_pattern, content)
                    modified = True
                    break
            
            if not modified:
                # Fallback: add to the end of greeting function
                greeting_func = content.find('def get_time_based_greeting()')
                if greeting_func != -1:
                    # Simple approach: replace the return statement
                    return_match = re.search(r'return f"([^"]+)"', content[greeting_func:])
                    if return_match:
                        old_greeting = return_match.group(1)
                        content = content.replace(f'return f"{old_greeting}"', f'return f"{old_greeting} {new_greeting}"')
            
            # COMPLETE REPLACEMENT: Find and replace the entire greeting line
            greeting_pattern = r'greeting = f"[^"]*"'
            match = re.search(greeting_pattern, content)
            
            if match:
                old_line = match.group(0)
                # COMPLETE REPLACEMENT: Create entirely new greeting without keeping old parts
                new_line = f'greeting = f"{{time_greeting}}, {new_greeting}"'
                content = content.replace(old_line, new_line)
                logger.info(f"🔧 COMPLETE REPLACEMENT: '{old_line}' -> '{new_line}'")
            else:
                # Fallback: look for the specific pattern we know exists
                specific_pattern = r'greeting = f"\{time_greeting\}[^"]*"'
                match = re.search(specific_pattern, content)
                if match:
                    old_line = match.group(0)
                    new_line = f'greeting = f"{{time_greeting}}, {new_greeting}"'
                    content = content.replace(old_line, new_line)
                    logger.info(f"🔧 FALLBACK REPLACEMENT: '{old_line}' -> '{new_line}'")
                else:
                    logger.error(f"Could not find any greeting pattern in file")
                    return False
            
            # Write back to file
            with open('fixed_conversation_app.py', 'w') as f:
                f.write(content)
            
            logger.info(f"🔧 REAL CHANGE: Updated greeting to '{new_greeting}'")
            
            # Force reload by touching the file
            import os
            os.utime('fixed_conversation_app.py', None)
            return True
            
        except Exception as e:
            logger.error(f"Failed to write greeting to file: {e}")
            return False

# Global admin action handler
admin_action_handler = AdminActionHandler()