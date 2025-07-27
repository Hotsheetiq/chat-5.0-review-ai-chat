"""
Create pre-recorded hold message audio
"""

import os
import requests
import logging
import shutil
from elevenlabs_integration import generate_elevenlabs_audio

def create_hold_message():
    """Create the 'Please hold' audio message"""
    hold_text = "Please hold on for a moment while I process that for you."
    
    try:
        # Generate audio file using ElevenLabs
        temp_audio_path = generate_elevenlabs_audio(hold_text, voice_id="f218e5pATi8cBqEEIGBU")
        
        if temp_audio_path:
            # Copy to static directory
            static_path = "static/please_hold.mp3"
            os.makedirs("static", exist_ok=True)
            shutil.copy2(temp_audio_path, static_path)
            
            # Clean up temp file
            os.unlink(temp_audio_path)
            
            logging.info(f"✅ Hold message audio created: {static_path}")
            return static_path
        else:
            logging.error("❌ Failed to generate hold audio")
            return None
            
    except Exception as e:
        logging.error(f"❌ Failed to create hold message: {e}")
        return None

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    create_hold_message()