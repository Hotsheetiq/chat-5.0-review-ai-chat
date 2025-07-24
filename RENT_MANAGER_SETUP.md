# Rent Manager API Integration Setup

## Current Status
- Phone number lookup: ❌ Not connected
- Tenant data: ❌ Using temporary test data
- API Integration: ❌ Need RENT_MANAGER_API_KEY

## To Connect Your Actual Rent Manager Data:

### Step 1: Get Your API Key
1. Log into your Rent Manager admin panel
2. Navigate to API settings or integrations
3. Generate or copy your API key
4. The key format should be like: `X-RM12Api-ApiToken`

### Step 2: Add to Replit Secrets
1. In Replit, go to Secrets tab (lock icon)
2. Add new secret:
   - Key: `RENT_MANAGER_API_KEY`
   - Value: [Your actual API key]

### Step 3: Automatic Benefits
Once connected, Tony will:
- Recognize your phone number instantly
- Greet you personally: "Hi [Your Name]! How can I help you in unit [X] today?"
- Create maintenance requests directly in your system
- Log all calls automatically
- Access your actual tenant database

### Current Temporary Setup
For testing, I've added a temporary lookup for phone: +1(347)743-0880
- Name: Test Tenant
- Unit: 4B
- Property: Main Property

This will be replaced with your real data once API key is provided.

## Webhook URL for Twilio
```
https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev/incoming-call
```