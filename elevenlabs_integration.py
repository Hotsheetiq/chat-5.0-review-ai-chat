"""
ElevenLabs Voice Generation Integration for Dimitry Junior AI
"""

import os
import requests
import tempfile
import logging
import time
import hashlib
from typing import Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# OPTIMIZED: Audio cache for performance
audio_cache = OrderedDict()
MAX_CACHE_SIZE = 100

# Available male voices from our ElevenLabs account
AVAILABLE_VOICES = {
    "adam": "pNInz6obpgDQGcFmaJgB",  # Professional American male
    "daniel": "onwK4e9ZLuTAKqWW03F9",  # Middle aged American male
    "sam": "yoZ06aMxZJJ28mfd3POQ",   # Warm American male
    "antoni": "ErXwobaYiN019PkySvjV", # Young American male
}

def generate_elevenlabs_audio(text: str, voice_id: str = None, voice_name: str = "adam", speed: float = 1.0) -> Optional[str]:
    """
    OPTIMIZED audio generation with caching, timing, and speed control
    """
    # ⏰ START ELEVENLABS TIMING
    elevenlabs_start = time.time()
    
    if not ELEVENLABS_API_KEY:
        logger.warning("ElevenLabs API key not available")
        return None
    
    # Use voice_id if provided, otherwise get from voice_name
    if not voice_id:
        voice_id = AVAILABLE_VOICES.get(voice_name, AVAILABLE_VOICES["adam"])
    
    # Check cache first for performance (include speed in cache key)
    cache_key = hashlib.md5(f"{text}_{voice_id}_{speed}".encode()).hexdigest()
    if cache_key in audio_cache:
        cached_path = audio_cache[cache_key]
        cache_time = time.time() - elevenlabs_start
        logger.info(f"[Timing] ElevenLabs cache hit: {cache_time:.3f} seconds")
        # Move to end (most recently used)
        audio_cache.move_to_end(cache_key)
        return cached_path
    
    try:
        url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        # Calculate speaking rate based on speed parameter (1.0 = normal, 1.15 = 15% faster)
        speaking_rate = min(1.5, max(0.5, speed))  # Clamp between 0.5x and 1.5x
        
        data = {
            "text": text,
            "model_id": "eleven_turbo_v2_5",  # Fastest model for real-time
            "voice_settings": {
                "stability": 0.85,        # VERY HIGH stability for absolutely consistent professional tone
                "similarity_boost": 0.90, # Maximum consistency for same voice character
                "style": 0.1,            # MINIMAL style for neutral, professional tone - no emotion variation
                "use_speaker_boost": True, # Enhanced clarity for phone calls
                "speaking_rate": speaking_rate  # Speed control for hold messages
            }
        }
        
        # OPTIMIZED: Reduced timeout for faster failure
        response = requests.post(url, json=data, headers=headers, timeout=3)
        
        if response.status_code == 200:
            # Save audio to temporary file and cache it
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as audio_file:
                audio_file.write(response.content)
                audio_path = audio_file.name
                
                # Cache the audio file path
                if len(audio_cache) >= MAX_CACHE_SIZE:
                    # Remove oldest entry
                    oldest_key, oldest_path = audio_cache.popitem(last=False)
                    try:
                        os.unlink(oldest_path)  # Delete old file
                    except:
                        pass
                
                audio_cache[cache_key] = audio_path
                
                # Log timing
                generation_time = time.time() - elevenlabs_start
                logger.info(f"[Timing] ElevenLabs generation: {generation_time:.3f} seconds")
                
                return audio_path
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
            logger.error(f"ElevenLabs voices API error: {response.status_code}")
            return []
            
    except Exception as e:
        logger.error(f"Error fetching ElevenLabs voices: {e}")
        return []

def get_voice_id_by_name(voice_name):
    """Get voice ID by name from available voices"""
    return AVAILABLE_VOICES.get(voice_name.lower(), AVAILABLE_VOICES["adam"])