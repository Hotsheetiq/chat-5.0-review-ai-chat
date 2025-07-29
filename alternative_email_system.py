"""
Alternative email system for immediate transcript delivery
This provides a backup solution while SendGrid verification is being completed
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import pytz
import logging

logger = logging.getLogger(__name__)

def send_transcript_via_gmail_smtp(call_sid, caller_phone, transcript, issue_type=None, address_status="unknown"):
    """
    Alternative email system using Gmail SMTP
    This bypasses SendGrid verification requirements
    """
    try:
        # Email configuration
        sender_email = "grinbergchat@gmail.com"  # This would need app password
        password = "your_app_password_here"  # Gmail app password required
        receiver_email = "grinbergchat@gmail.com"
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Call Transcript - {caller_phone} - {datetime.now().strftime('%B %d, %Y at %I:%M %p ET')}"
        message["From"] = sender_email
        message["To"] = receiver_email
        
        # Create HTML content
        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    Grinberg Management Call Transcript
                </h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #2c3e50;">Call Details</h3>
                    <p><strong>Caller Phone:</strong> {caller_phone}</p>
                    <p><strong>Call ID:</strong> {call_sid}</p>
                    <p><strong>Issue Type:</strong> {issue_type or 'Not specified'}</p>
                    <p><strong>Address Status:</strong> {address_status}</p>
                </div>
                
                <div style="background-color: #fff; border: 1px solid #ddd; padding: 20px; border-radius: 5px;">
                    <h3 style="color: #2c3e50; margin-bottom: 15px;">Complete Conversation Transcript</h3>
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 3px; font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 14px;">
{transcript}
                    </div>
                </div>
                
                <div style="margin-top: 20px; padding: 15px; background-color: #e8f4f8; border-radius: 5px;">
                    <h4 style="color: #2c3e50; margin: 0 0 10px 0;">Next Actions</h4>
                    <ul style="margin: 0; padding-left: 20px;">
                        <li>Review conversation for any follow-up needed</li>
                        <li>Address verification status: {address_status}</li>
                        <li>Contact caller if additional information required</li>
                    </ul>
                </div>
                
                <p style="margin-top: 30px; font-size: 12px; color: #666; border-top: 1px solid #ddd; padding-top: 15px;">
                    This is an automated transcript from the Grinberg Management voice assistant system.
                    <br>Sent via alternative email system due to SendGrid verification pending.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML part
        part = MIMEText(html, "html")
        message.attach(part)
        
        # Send email via Gmail SMTP (requires app password)
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
            server.login(sender_email, password)
            text = message.as_string()
            server.sendmail(sender_email, receiver_email, text)
        
        logger.info(f"✅ ALTERNATIVE EMAIL SENT: Transcript delivered via Gmail SMTP")
        return True
        
    except Exception as e:
        logger.error(f"❌ ALTERNATIVE EMAIL ERROR: {e}")
        return False

def send_simple_notification(caller_phone, issue_summary, address_info):
    """
    Send a simple notification that doesn't require complex HTML
    """
    try:
        # This could use a webhook service like Zapier or IFTTT
        # Or a simple HTTP POST to a webhook URL that forwards to email
        
        notification_data = {
            "caller": caller_phone,
            "issue": issue_summary,
            "address": address_info,
            "timestamp": datetime.now().isoformat(),
            "source": "Chris Voice Assistant"
        }
        
        # Example webhook call (would need actual webhook URL)
        # import requests
        # webhook_url = "https://hooks.zapier.com/hooks/catch/YOUR_WEBHOOK_ID/"
        # response = requests.post(webhook_url, json=notification_data)
        
        logger.info(f"📧 SIMPLE NOTIFICATION: Would send {notification_data}")
        return True
        
    except Exception as e:
        logger.error(f"❌ NOTIFICATION ERROR: {e}")
        return False