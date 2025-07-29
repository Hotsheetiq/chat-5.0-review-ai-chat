#!/usr/bin/env python3
"""
Debug SendGrid API and delivery status
"""
import os
import json
import requests
from datetime import datetime

def check_sendgrid_status():
    api_key = os.environ.get('SENDGRID_API_KEY')
    if not api_key:
        print("❌ SENDGRID_API_KEY not found")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    print("🔍 SENDGRID ACCOUNT STATUS CHECK")
    print("=" * 50)
    
    # Check account status
    try:
        response = requests.get('https://api.sendgrid.com/v3/user/account', headers=headers)
        print(f"Account Status: {response.status_code}")
        if response.status_code == 200:
            account_data = response.json()
            print(f"Account Type: {account_data.get('type', 'Unknown')}")
            print(f"Account Reputation: {account_data.get('reputation', 'Unknown')}")
        else:
            print(f"Account Error: {response.text}")
    except Exception as e:
        print(f"Account Check Failed: {e}")
    
    # Check sender authentication
    try:
        response = requests.get('https://api.sendgrid.com/v3/verified_senders', headers=headers)
        print(f"\nSender Verification: {response.status_code}")
        if response.status_code == 200:
            senders = response.json().get('results', [])
            for sender in senders:
                print(f"Sender: {sender.get('from_email')} - Verified: {sender.get('verified')}")
        else:
            print(f"Sender Error: {response.text}")
    except Exception as e:
        print(f"Sender Check Failed: {e}")
    
    # Check mail settings
    try:
        response = requests.get('https://api.sendgrid.com/v3/mail_settings', headers=headers)
        print(f"\nMail Settings: {response.status_code}")
        if response.status_code == 200:
            settings = response.json()
            print(f"Settings: {json.dumps(settings, indent=2)}")
    except Exception as e:
        print(f"Settings Check Failed: {e}")
    
    # Send a direct test email
    print(f"\n📧 SENDING DIRECT TEST EMAIL")
    print("=" * 50)
    
    test_email_data = {
        "personalizations": [
            {
                "to": [{"email": "grinbergchat@gmail.com"}],
                "subject": f"SendGrid Test - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            }
        ],
        "from": {"email": "grinbergchat@gmail.com"},
        "content": [
            {
                "type": "text/plain",
                "value": f"This is a direct SendGrid API test sent at {datetime.now().isoformat()}\n\nIf you receive this, SendGrid is working correctly."
            }
        ]
    }
    
    try:
        response = requests.post(
            'https://api.sendgrid.com/v3/mail/send',
            headers=headers,
            json=test_email_data
        )
        print(f"Test Email Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        if response.status_code != 202:
            print(f"Error Response: {response.text}")
        else:
            print("✅ Test email sent successfully!")
            print("Check grinbergchat@gmail.com (including spam folder)")
    except Exception as e:
        print(f"Test Email Failed: {e}")

if __name__ == "__main__":
    check_sendgrid_status()