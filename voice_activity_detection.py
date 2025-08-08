"""
Voice Activity Detection (VAD) for real-time conversation handling
Detects when user starts/stops speaking for seamless turn-taking
"""

import numpy as np
import logging
from typing import Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)

class VoiceActivityDetector:
    def __init__(self):
        self.silence_threshold = 0.01  # Amplitude threshold for silence
        self.min_speech_duration = 0.3  # Minimum seconds to consider as speech
        self.silence_duration_for_end = 0.8  # Seconds of silence to end turn
        self.sample_rate = 8000  # Twilio audio sample rate
        
        # State tracking
        self.is_speaking = False
        self.speech_start_time = None
        self.last_sound_time = None
        self.audio_buffer = []
        
    def process_audio_chunk(self, audio_data: bytes) -> Tuple[bool, bool]:
        """
        Process audio chunk and return (is_speaking, speech_ended)
        
        Returns:
            is_speaking: True if user is currently speaking
            speech_ended: True if user just finished speaking (turn ended)
        """
        try:
            # Convert audio bytes to numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Normalize to 0-1 range
            if len(audio_array) > 0:
                audio_normalized = np.abs(audio_array.astype(np.float32)) / 32768.0
                amplitude = np.mean(audio_normalized)
            else:
                amplitude = 0.0
            
            current_time = asyncio.get_event_loop().time()
            
            # Detect if there's significant audio activity
            has_sound = amplitude > self.silence_threshold
            
            if has_sound:
                self.last_sound_time = current_time
                
                if not self.is_speaking:
                    # Speech is starting
                    self.speech_start_time = current_time
                    self.is_speaking = True
                    logger.debug("Speech detected - user started speaking")
                    return True, False
                else:
                    # Continue speaking
                    return True, False
            else:
                # No significant sound detected
                if self.is_speaking and self.last_sound_time:
                    silence_duration = current_time - self.last_sound_time
                    
                    if silence_duration >= self.silence_duration_for_end:
                        # User stopped speaking
                        speech_duration = current_time - self.speech_start_time if self.speech_start_time else 0
                        
                        if speech_duration >= self.min_speech_duration:
                            # Valid speech turn ended
                            self.is_speaking = False
                            self.speech_start_time = None
                            logger.debug(f"Speech ended - duration: {speech_duration:.2f}s")
                            return False, True
                        else:
                            # Too short to be real speech, ignore
                            self.is_speaking = False
                            self.speech_start_time = None
                            return False, False
                
                return self.is_speaking, False
                
        except Exception as e:
            logger.error(f"VAD processing error: {e}")
            return False, False
    
    def reset(self):
        """Reset VAD state for new call"""
        self.is_speaking = False
        self.speech_start_time = None
        self.last_sound_time = None
        self.audio_buffer.clear()
        logger.debug("VAD state reset")
    
    def adjust_sensitivity(self, sensitivity: float):
        """Adjust VAD sensitivity (0.0 = most sensitive, 1.0 = least sensitive)"""
        self.silence_threshold = 0.005 + (sensitivity * 0.02)  # Range: 0.005 to 0.025
        logger.info(f"VAD sensitivity adjusted to {sensitivity}, threshold: {self.silence_threshold}")
    
    def get_status(self) -> dict:
        """Get current VAD status for monitoring"""
        return {
            "is_speaking": self.is_speaking,
            "silence_threshold": self.silence_threshold,
            "speech_duration": asyncio.get_event_loop().time() - self.speech_start_time if self.speech_start_time else 0
        }

# Global VAD instance
vad_detector = VoiceActivityDetector()