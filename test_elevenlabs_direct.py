#!/usr/bin/env python3
import requests
import os

def test_elevenlabs_direct():
    """Test ElevenLabs API directly"""
    
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("❌ No ElevenLabs API key found")
        return
    
    voice_id = "pNInz6obpgDQGcFmaJgB"  # Chris voice
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key.strip().strip('"')
    }
    
    data = {
        "text": "Hi there, you've reached Grinberg Management. I'm Chris, how can I help you today?",
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {
            "stability": 0.75,
            "similarity_boost": 0.85,
            "style": 0.25,
            "use_speaker_boost": True
        }
    }
    
    try:
        print("Testing ElevenLabs API...")
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ ElevenLabs API working!")
            # Save test audio
            with open("test_chris_voice.mp3", "wb") as f:
                f.write(response.content)
            print("✅ Test audio saved as test_chris_voice.mp3")
            return True
        else:
            print(f"❌ ElevenLabs error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_elevenlabs_direct()