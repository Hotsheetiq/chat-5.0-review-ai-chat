"""
Email Call Summary System
Sends detailed call summaries after each call session ends
"""

import os
import json
import logging
from datetime import datetime
import pytz
from typing import Dict, Any, Optional
import sendgrid
from sendgrid.helpers.mail import Mail

logger = logging.getLogger(__name__)

class EmailCallSummary:
    def __init__(self):
        self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
        self.owner_email = os.environ.get('OWNER_EMAIL', 'notifications@grinbergmanagement.com')
        
    def determine_priority_label(self, reported_issue: str, conversation_content: str) -> str:
        """Determine priority label based on official business rules"""
        if not reported_issue and not conversation_content:
            return "STANDARD"
            
        content_lower = f"{reported_issue} {conversation_content}".lower()
        
        # EMERGENCY - matches 24/7 emergencies from business rules
        emergency_keywords = [
            'no heat', 'heating not working', 'heat not working', 'no heating',
            'flooding', 'flood', 'water everywhere', 'water damage',
            'clogged toilet', 'sewer backup', 'toilet overflowing', 'sewage',
            'fire', 'smoke', 'life threatening', 'danger', 'emergency'
        ]
        
        for keyword in emergency_keywords:
            if keyword in content_lower:
                return "EMERGENCY"
        
        # URGENT - explicit urgent requests
        urgent_keywords = [
            'urgent', 'asap', 'immediately', 'right away', 'can\'t wait'
        ]
        
        for keyword in urgent_keywords:
            if keyword in content_lower:
                return "URGENT"
                
        return "STANDARD"
    
    def format_subject(self, priority_label: str, address: str, issue: str, ticket_id: Optional[str] = None) -> str:
        """Format email subject according to specifications"""
        address_part = address if address and address != 'unknown' else "Address Unknown"
        
        # Truncate issue to reasonable length for subject
        issue_short = issue[:50] + "..." if len(issue) > 50 else issue
        
        ticket_part = f"Ticket {ticket_id}" if ticket_id else "No Ticket"
        
        return f"[{priority_label}] {address_part} — {issue_short} — {ticket_part}"
    
    def format_email_body(self, call_data: Dict[str, Any]) -> str:
        """Format comprehensive email body according to specifications"""
        
        # Extract data with safe defaults
        session_facts = call_data.get('session_facts', {})
        conversation_history = call_data.get('conversation_history', [])
        rent_manager_results = call_data.get('rent_manager_results', {})
        
        # Format timestamp
        eastern = pytz.timezone('America/New_York')
        call_time = datetime.fromtimestamp(call_data.get('timestamp', datetime.now().timestamp()), tz=eastern)
        formatted_time = call_time.strftime('%Y-%m-%d %I:%M:%S %p %Z')
        
        # Determine office status
        office_status = "Closed" if call_time.hour < 9 or call_time.hour >= 17 or call_time.weekday() >= 5 else "Open"
        
        # Get transcript snippet
        transcript_lines = [msg.get('message', '') for msg in conversation_history if msg.get('message')]
        first_lines = " / ".join(transcript_lines[:2]) if len(transcript_lines) >= 2 else transcript_lines[0] if transcript_lines else "No transcript"
        last_lines = " / ".join(transcript_lines[-2:]) if len(transcript_lines) >= 2 else transcript_lines[-1] if transcript_lines else "No transcript"
        
        body = f"""
=== CALL SUMMARY ===

Date/Time: {formatted_time}
Call Mode: {call_data.get('call_mode', 'Default')}
Office Status: {office_status}
Priority: {call_data.get('priority_label', 'STANDARD')}

=== CALLER & PROPERTY ===

Caller Name: {session_facts.get('contactName', 'Unknown')}
Callback Number: {session_facts.get('callbackNumber', 'Unknown')}
Address: {session_facts.get('propertyAddress', 'Unknown')}
Unit: {session_facts.get('unitNumber', 'Unknown')}
Tenant Linked: {call_data.get('tenant_linked', 'Unknown')}
Tenant ID: {call_data.get('tenant_id', 'Unknown')}

=== ISSUE DETAILS ===

Reported Issue: {session_facts.get('reportedIssue', 'No specific issue reported')}
Description: {call_data.get('issue_description', 'See conversation transcript')}
Access Instructions: {session_facts.get('accessInstructions', 'None provided')}

=== RENT MANAGER RESULTS ===

Property ID: {rent_manager_results.get('propertyId', 'Not found')}
Unit ID: {rent_manager_results.get('unitId', 'Not found')}
Tenant ID: {rent_manager_results.get('tenantId', 'Not found')}

Ticket Created: {call_data.get('ticket_created', 'No')}
Ticket ID: {call_data.get('ticket_id', 'N/A')}
Ticket Priority: {call_data.get('ticket_priority', 'N/A')}
Creation Status: {call_data.get('ticket_status', 'No ticket creation attempted')}

=== NEXT ACTIONS ===

System Response: {call_data.get('system_response', 'Standard issue logging and dispatch')}
Manual Follow-ups: {call_data.get('manual_followups', 'None identified')}

=== TRANSCRIPT SNIPPET ===

First Exchange: {first_lines}
...
Last Exchange: {last_lines}

=== TECHNICAL DETAILS ===

Call Duration: {call_data.get('call_duration', 'Unknown')}
Response Latency: {call_data.get('latency_notes', 'Not measured')}
Call ID: {call_data.get('call_sid', 'Unknown')}

--- End of Call Summary ---
"""
        return body.strip()
    
    def send_call_summary(self, call_data: Dict[str, Any]) -> bool:
        """Send call summary email with proper priority and formatting"""
        try:
            # Determine priority
            reported_issue = call_data.get('session_facts', {}).get('reportedIssue', '')
            conversation_content = ' '.join([msg.get('message', '') for msg in call_data.get('conversation_history', [])])
            priority_label = self.determine_priority_label(reported_issue, conversation_content)
            call_data['priority_label'] = priority_label
            
            # Format subject and body
            address = call_data.get('session_facts', {}).get('propertyAddress', 'Unknown')
            issue = reported_issue or 'General inquiry'
            ticket_id = call_data.get('ticket_id')
            
            subject = self.format_subject(priority_label, address, issue, ticket_id)
            body = self.format_email_body(call_data)
            
            # Create and send email
            message = Mail(
                from_email='noreply@grinbergmanagement.com',
                to_emails=self.owner_email,
                subject=subject,
                plain_text_content=body
            )
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Call summary email sent successfully: {subject}")
                return True
            else:
                logger.error(f"Failed to send call summary email: {response.status_code} - {response.body}")
                return False
                
        except Exception as e:
            logger.error(f"EMAIL SEND FAILED: {str(e)}")
            return False
    
    def send_emergency_alert(self, call_data: Dict[str, Any]) -> bool:
        """Send immediate emergency alert for priority emergencies"""
        if call_data.get('priority_label') == 'EMERGENCY':
            # Add urgent flag to subject
            call_data_copy = call_data.copy()
            call_data_copy['urgent_alert'] = True
            
            subject_parts = self.format_subject(
                "EMERGENCY ALERT",
                call_data.get('session_facts', {}).get('propertyAddress', 'Unknown'),
                call_data.get('session_facts', {}).get('reportedIssue', 'Emergency situation'),
                call_data.get('ticket_id')
            )
            
            alert_body = f"""
🚨 EMERGENCY ALERT 🚨

{self.format_email_body(call_data)}

*** This is an emergency situation requiring immediate attention ***
"""
            
            try:
                message = Mail(
                    from_email='emergency@grinbergmanagement.com',
                    to_emails=self.owner_email,
                    subject=f"🚨 {subject_parts}",
                    plain_text_content=alert_body
                )
                
                response = self.sendgrid_client.send(message)
                return response.status_code in [200, 201, 202]
            except Exception as e:
                logger.error(f"EMERGENCY EMAIL SEND FAILED: {str(e)}")
                return False
        
        return True  # Not an emergency, no alert needed

# Global instance
email_summary_system = EmailCallSummary()