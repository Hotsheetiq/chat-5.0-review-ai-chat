#!/usr/bin/env python3
"""
Simple email test to bypass encoding issues
"""
import os
import json
import requests
from datetime import datetime
import pytz

def send_simple_email():
    """Send a simple test email using direct HTTP request to bypass encoding issues"""
    
    # Get API key
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        return {"status": "error", "message": "No API key"}
    
    # Get Eastern Time
    eastern = pytz.timezone('US/Eastern')
    now = eastern.localize(datetime.now())
    timestamp = now.strftime("%B %d, %Y at %I:%M %p ET")
    
    # Simple email data
    email_data = {
        "personalizations": [
            {
                "to": [{"email": "grinbergchat@gmail.com"}],
                "subject": f"Test Email - {timestamp}"
            }
        ],
        "from": {"email": "grinbergchat@gmail.com"},
        "content": [
            {
                "type": "text/plain",
                "value": f"""
Test email from Grinberg Management Voice Assistant

Timestamp: {timestamp}
Status: SendGrid verification complete
Test Type: Direct HTTP request

This confirms the email system is working properly.

Next step: All Chris email promises will now be fulfilled automatically.
                """
            }
        ]
    }
    
    # Send via direct HTTP request
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers=headers,
            json=email_data,
            timeout=10
        )
        
        if response.status_code == 202:
            return {
                "status": "success", 
                "message": f"Email sent successfully (Code: {response.status_code})",
                "timestamp": timestamp
            }
        else:
            return {
                "status": "error", 
                "message": f"SendGrid error: {response.status_code} - {response.text}",
                "response": response.text
            }
            
    except Exception as e:
        return {"status": "error", "message": f"Request failed: {str(e)}"}

if __name__ == "__main__":
    result = send_simple_email()
    print(json.dumps(result, indent=2))