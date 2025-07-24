"""
ElevenLabs Voice Generation Integration for Dimitry Junior AI
"""

import os
import requests
import tempfile
import logging
from typing import Optional

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Available male voices from our ElevenLabs account
AVAILABLE_VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",  # Professional American male
    "daniel": "onwK4e9ZLuTAKqWW03F9",  # Middle aged American male
    "sam": "yoZ06aMxZJJ28mfd3POQ",   # Warm American male
    "antoni": "ErXwobaYiN019PkySvjV", # Young American male
}

def generate_elevenlabs_audio(text: str, voice_id: str = None, voice_name: str = "adam") -> Optional[str]:
    """
    Generate audio using ElevenLabs API and return URL or file path
    """
    if not ELEVENLABS_API_KEY:
        logger.warning("ElevenLabs API key not available")
        return None
    
    # Use voice_id if provided, otherwise get from voice_name
    if not voice_id:
        voice_id = AVAILABLE_VOICES.get(voice_name, AVAILABLE_VOICES["adam"])
    
    try:
        url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",  # Fastest model for real-time
            "voice_settings": {
                "stability": 0.15,        # Very low for maximum naturalness
                "similarity_boost": 0.85, # High to maintain voice character
                "style": 0.10,           # Minimal for fastest, most natural speech
                "use_speaker_boost": True # Enhanced clarity for phone calls
            }
        }
        
        response = requests.post(url, json=data, headers=headers, timeout=5)  # Reduced timeout for speed
        
        if response.status_code == 200:
            # Save audio to temporary file and return path
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_file:
                audio_file.write(response.content)
                return audio_file.name
        else:
            logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error generating ElevenLabs audio: {e}")
        return None

def get_voice_list():
    """Get list of available voices from ElevenLabs"""
    if not ELEVENLABS_API_KEY:
        return []
    
    try:
        url = f"{ELEVENLABS_BASE_URL}/voices"
        headers = {"xi-api-key": ELEVENLABS_API_KEY}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            voices_data = response.json()
            return voices_data.get("voices", [])
        else:
            logger.error(f"Error fetching voices: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching voice list: {e}")
        return []

def test_elevenlabs_connection():
    """Test ElevenLabs API connection"""
    if not ELEVENLABS_API_KEY:
        return False, "No API key"
    
    try:
        voices = get_voice_list()
        if voices:
            return True, f"Connected - {len(voices)} voices available"
        else:
            return False, "API key invalid or no voices"
    except Exception as e:
        return False, f"Connection error: {e}"