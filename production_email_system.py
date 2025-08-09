"""
Production Email System - Call Summary and Emergency Alerts
Implements email summaries with proper subject formatting and de-duplication
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional
import pytz

logger = logging.getLogger(__name__)

class ProductionEmailSystem:
    def __init__(self):
        self.sent_emails = set()  # Track sent emails for de-duplication
        self.sendgrid_api_key = os.environ.get('SENDGRID_API_KEY')
        
    def send_call_summary_on_end(self, call_sid: str, session_data: Dict) -> bool:
        """
        Send call summary email when call ends
        Implements subject formatting rules and de-duplication
        """
        try:
            # Check for de-duplication
            if call_sid in self.sent_emails:
                logger.info(f"Email already sent for call {call_sid}")
                return True
            
            # Extract call data
            facts = session_data.get('session_facts', {})
            conversation_history = session_data.get('conversation_history', [])
            
            # Determine issue type and priority
            issue_type = facts.get('reportedIssue', 'General Inquiry')
            priority = facts.get('priority', 'Standard')
            address = facts.get('propertyAddress', 'Unverified')
            verified_property = facts.get('verified_property', False)
            ticket_id = facts.get('ticketId', None)
            
            # Format address status
            if verified_property and address != 'Unverified':
                address_status = f"Verified: {address}"
            elif address != 'Unverified':
                address_status = f"Unverified: {address}"
            else:
                address_status = "No address provided"
            
            # Generate subject based on priority
            subject = self._generate_email_subject(priority, issue_type, address, call_sid)
            
            # Generate email body
            body = self._generate_email_body(
                call_sid, facts, conversation_history, address_status, ticket_id
            )
            
            # Send email
            success = self._send_email(subject, body)
            
            if success:
                self.sent_emails.add(call_sid)
                logger.info(f"📧 Call summary sent for {call_sid}: {subject}")
            
            return success
            
        except Exception as e:
            logger.error(f"Call summary email failed: {e}")
            return False
    
    def send_emergency_alert(self, call_sid: str, emergency_data: Dict) -> bool:
        """
        Send immediate emergency alert email
        """
        try:
            issue_type = emergency_data.get('issue', 'Emergency')
            address = emergency_data.get('address', 'Unknown Location')
            contact = emergency_data.get('contact_name', 'Unknown Caller')
            phone = emergency_data.get('contact_phone', 'Unknown')
            
            subject = f"🚨 EMERGENCY – {issue_type} – {address} – {call_sid}"
            
            body = f"""
EMERGENCY ALERT - IMMEDIATE ATTENTION REQUIRED

Call ID: {call_sid}
Emergency Type: {issue_type}
Location: {address}
Caller: {contact}
Phone: {phone}

Time: {datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S ET')}

This emergency requires 24/7 dispatch according to company policy.

EMERGENCY TYPES REQUIRING IMMEDIATE RESPONSE:
- No heat
- Flooding
- Clogged toilet or sewer backup

Action Required: Dispatch emergency maintenance immediately.
"""
            
            success = self._send_email(subject, body)
            
            if success:
                logger.info(f"🚨 Emergency alert sent for {call_sid}")
            
            return success
            
        except Exception as e:
            logger.error(f"Emergency alert email failed: {e}")
            return False
    
    def _generate_email_subject(self, priority: str, issue_type: str, address: str, call_sid: str) -> str:
        """Generate email subject based on priority rules"""
        address_text = address if address != 'Unverified' else 'Unverified'
        
        if priority == 'Emergency':
            return f"EMERGENCY – {issue_type} – {address_text} – {call_sid}"
        elif priority == 'Urgent':
            return f"URGENT – {issue_type} – {address_text} – {call_sid}"
        else:
            return f"SUMMARY – {issue_type} – {address_text} – {call_sid}"
    
    def _generate_email_body(self, call_sid: str, facts: Dict, conversation_history: List, 
                           address_status: str, ticket_id: Optional[str]) -> str:
        """Generate comprehensive email body"""
        
        timestamp = datetime.now(pytz.timezone('America/New_York')).strftime('%Y-%m-%d %H:%M:%S ET')
        
        # Build facts summary
        facts_summary = []
        for key, value in facts.items():
            if value and key in ['contactName', 'callbackNumber', 'unitNumber', 'reportedIssue', 'accessInstructions']:
                display_key = key.replace('Name', ' Name').replace('Number', ' Number').replace('Issue', ' Issue')
                facts_summary.append(f"{display_key}: {value}")
        
        # Build conversation transcript
        transcript_lines = []
        for turn in conversation_history:
            speaker = turn.get('speaker', 'Unknown')
            message = turn.get('message', '')
            turn_time = turn.get('timestamp', timestamp)
            transcript_lines.append(f"[{turn_time}] {speaker}: {message}")
        
        transcript = "\n".join(transcript_lines) if transcript_lines else "No conversation recorded"
        
        # Build ticket status
        ticket_status = f"Ticket Created: {ticket_id}" if ticket_id else "No ticket created"
        
        body = f"""
PROPERTY MANAGEMENT CALL SUMMARY

Call Details:
Call ID: {call_sid}
Timestamp: {timestamp}
Priority: {facts.get('priority', 'Standard')}

Caller Information:
{chr(10).join(facts_summary) if facts_summary else 'No caller information collected'}

Property Information:
{address_status}

Service Request:
{ticket_status}

Full Conversation Transcript:
{transcript}

---
Generated by Chris - Grinberg Management Voice Assistant
"""
        
        return body
    
    def _send_email(self, subject: str, body: str) -> bool:
        """Send email using SendGrid"""
        try:
            if not self.sendgrid_api_key:
                logger.warning("SendGrid API key not configured")
                return False
            
            import sendgrid
            from sendgrid.helpers.mail import Mail
            
            sg = sendgrid.SendGridAPIClient(api_key=self.sendgrid_api_key)
            
            # Get recipient from environment or use default
            to_email = os.environ.get('SUMMARY_EMAIL_RECIPIENT', 'management@grinbergproperties.com')
            from_email = os.environ.get('FROM_EMAIL', 'chris@grinbergproperties.com')
            
            message = Mail(
                from_email=from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=body
            )
            
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                return True
            else:
                logger.error(f"SendGrid error: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Email sending failed: {e}")
            return False

# Global email system instance
production_email_system = ProductionEmailSystem()

# Export functions for backward compatibility
def send_call_transcript_email(call_sid: str, session_data: Dict) -> bool:
    """Backward compatibility function"""
    return production_email_system.send_call_summary_on_end(call_sid, session_data)

def send_call_summary_on_end(call_sid: str, session_data: Dict) -> bool:
    """Main function for call end email summaries"""
    return production_email_system.send_call_summary_on_end(call_sid, session_data)

def send_emergency_alert(call_sid: str, emergency_data: Dict) -> bool:
    """Send emergency alert email"""
    return production_email_system.send_emergency_alert(call_sid, emergency_data)