"""
Call End Handler - Triggers email summaries when calls end
"""

import logging
from datetime import datetime
import pytz
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

def send_call_summary_on_end(call_sid: str, conversation_history: Dict, openai_manager, email_summary_system) -> bool:
    """
    Send comprehensive call summary when call ends
    Called from Twilio webhook or timeout scenarios
    """
    try:
        if not email_summary_system:
            logger.warning("Email summary system not available")
            return False
            
        if call_sid not in conversation_history or not conversation_history[call_sid]:
            logger.warning(f"No conversation history found for call {call_sid}")
            return False
        
        # Get session facts from OpenAI manager
        session_facts = {}
        if openai_manager and hasattr(openai_manager, 'get_session_facts'):
            session_facts = openai_manager.get_session_facts(call_sid)
        
        # Build call data structure for email
        call_data = {
            'call_sid': call_sid,
            'timestamp': datetime.now().timestamp(),
            'session_facts': session_facts,
            'conversation_history': conversation_history[call_sid],
            'call_mode': 'Default',  # Could be enhanced to track actual mode used
            'call_duration': _calculate_call_duration(conversation_history[call_sid]),
            'system_response': _extract_system_response(conversation_history[call_sid]),
            'issue_description': _extract_issue_description(conversation_history[call_sid]),
            'rent_manager_results': {},  # Would be populated by actual RM integration
            'ticket_created': 'No',  # Would be updated by actual ticket creation
            'ticket_id': None,
            'ticket_status': 'No ticket creation attempted - after hours non-emergency',
            'manual_followups': _identify_manual_followups(session_facts, conversation_history[call_sid]),
            'latency_notes': 'See application logs for response times',
            'tenant_linked': 'Unknown',  # Would be determined by RM lookup
            'tenant_id': 'Unknown'
        }
        
        # Send the email summary
        success = email_summary_system.send_call_summary(call_data)
        
        # Send emergency alert if needed
        if call_data.get('priority_label') == 'EMERGENCY':
            emergency_success = email_summary_system.send_emergency_alert(call_data)
            logger.info(f"Emergency alert sent: {emergency_success}")
        
        if success:
            logger.info(f"Call summary email sent successfully for call {call_sid}")
        else:
            logger.error(f"EMAIL SEND FAILED for call {call_sid}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error sending call summary for {call_sid}: {str(e)}")
        return False

def _calculate_call_duration(conversation_messages: list) -> str:
    """Calculate call duration from conversation timestamps"""
    try:
        if len(conversation_messages) < 2:
            return "Less than 1 minute"
            
        first_msg = conversation_messages[0].get('timestamp', '')
        last_msg = conversation_messages[-1].get('timestamp', '')
        
        if not first_msg or not last_msg:
            return "Duration unknown"
            
        # Parse timestamps
        first_time = datetime.fromisoformat(first_msg.replace('Z', '+00:00'))
        last_time = datetime.fromisoformat(last_msg.replace('Z', '+00:00'))
        
        duration = last_time - first_time
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        
        return f"{minutes}m {seconds}s"
        
    except Exception:
        return "Duration calculation failed"

def _extract_system_response(conversation_messages: list) -> str:
    """Extract what the system told the caller about next steps"""
    system_responses = []
    
    for msg in conversation_messages:
        if msg.get('speaker') == 'Chris':
            message = msg.get('message', '').lower()
            # Look for key phrases about next steps
            if any(phrase in message for phrase in [
                'closed', 'business hours', 'call back', 'dispatch', 'logged', 'emergency'
            ]):
                system_responses.append(msg.get('message', ''))
    
    if system_responses:
        return ' | '.join(system_responses[-2:])  # Last couple of relevant responses
    
    return "Standard issue logging and dispatch"

def _extract_issue_description(conversation_messages: list) -> str:
    """Extract comprehensive issue description from conversation"""
    issue_parts = []
    
    for msg in conversation_messages:
        if msg.get('speaker') == 'Caller':
            message = msg.get('message', '').lower()
            # Look for issue-related keywords
            if any(keyword in message for keyword in [
                'problem', 'issue', 'broken', 'not working', 'leaking', 'heat', 'cold',
                'electrical', 'plumbing', 'repair', 'fix', 'maintenance'
            ]):
                issue_parts.append(msg.get('message', ''))
    
    if issue_parts:
        return ' | '.join(issue_parts[:3])  # First few issue descriptions
    
    return "See conversation transcript for details"

def _identify_manual_followups(session_facts: Dict, conversation_messages: list) -> str:
    """Identify what manual follow-ups might be needed"""
    followups = []
    
    # Check if address needs verification
    if not session_facts.get('propertyAddress') or session_facts.get('propertyAddress') == 'unknown':
        followups.append("Address verification needed")
    
    # Check if contact info is incomplete
    if not session_facts.get('contactName'):
        followups.append("Contact name missing")
    
    if not session_facts.get('callbackNumber'):
        followups.append("Callback number missing")
    
    # Check conversation for policy questions
    conversation_text = ' '.join([msg.get('message', '') for msg in conversation_messages]).lower()
    if any(phrase in conversation_text for phrase in ['refund', 'credit', 'policy', 'guarantee']):
        followups.append("Policy clarification may be needed")
    
    return ', '.join(followups) if followups else "None identified"