#!/usr/bin/env python3
"""
Update Twilio webhook URL to current Replit domain
"""
import os
import requests
from requests.auth import HTTPBasicAuth

# Twilio credentials
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
PHONE_NUMBER_SID = "PN3dbbe05ce3ee8a2329a5f75083831602"

# Current Replit domain
CURRENT_DOMAIN = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev"

def update_webhook():
    """Update Twilio webhook URL"""
    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/IncomingPhoneNumbers/{PHONE_NUMBER_SID}.json"
    
    data = {
        "VoiceUrl": f"{CURRENT_DOMAIN}/voice"
    }
    
    auth = HTTPBasicAuth(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    try:
        response = requests.post(url, data=data, auth=auth)
        
        if response.status_code == 200:
            print("✅ Webhook URL updated successfully!")
            print(f"New URL: {CURRENT_DOMAIN}/voice")
            return True
        else:
            print(f"❌ Error updating webhook: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception updating webhook: {e}")
        return False

if __name__ == "__main__":
    print(f"Updating Twilio webhook to: {CURRENT_DOMAIN}/voice")
    update_webhook()