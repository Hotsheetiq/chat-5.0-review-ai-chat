"""
Create the "Please hold" audio file using ElevenLabs
"""

import os
import requests
import logging

def create_hold_audio():
    """Create the hold message audio file"""
    try:
        ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
        if not ELEVENLABS_API_KEY:
            logging.error("ELEVENLABS_API_KEY not found")
            return False
        
        # Use Chris's voice for the hold message
        CHRIS_VOICE_ID = "f218e5pATi8cBqEEIGBU"
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{CHRIS_VOICE_ID}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": "Please hold on for a moment while I process that for you.",
            "model_id": "eleven_turbo_v2_5",
            "voice_settings": {
                "stability": 0.15,
                "similarity_boost": 0.85,
                "style": 0.2,
                "use_speaker_boost": True
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Save audio file
            with open('static/please_hold.mp3', 'wb') as f:
                f.write(response.content)
            
            logging.info("✅ Hold audio file created successfully: static/please_hold.mp3")
            return True
        else:
            logging.error(f"❌ Failed to create hold audio: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error creating hold audio: {e}")
        return False

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_hold_audio()