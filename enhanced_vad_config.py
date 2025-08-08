"""
Enhanced Voice Activity Detection Configuration
Optimized for ultra-fast response times (500-700ms silence timeout)
"""

import logging

logger = logging.getLogger(__name__)

class VADConfig:
    """Voice Activity Detection configuration for fast responses"""
    
    # Ultra-fast VAD settings for sub-1-second responses
    SILENCE_TIMEOUT = 600  # 600ms - reduced from default 1500ms
    SPEECH_TIMEOUT = 4000  # 4 seconds max speech duration
    CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for speech recognition
    
    # Audio processing settings
    SAMPLE_RATE = 16000
    CHUNK_SIZE = 1024
    
    # Performance optimization
    PROCESSING_DELAY = 50  # 50ms processing buffer
    MIN_SPEECH_LENGTH = 300  # 300ms minimum speech to process
    
    @classmethod
    def get_twilio_gather_config(cls) -> dict:
        """Get optimized Twilio Gather configuration for fast VAD"""
        return {
            'input': 'speech',
            'timeout': 8,  # Overall timeout
            'speechTimeout': int(cls.SILENCE_TIMEOUT / 1000),  # Convert to seconds
            'language': 'en-US',
            'enhanced': True,  # Use enhanced speech recognition
            'profanityFilter': False,  # Disable for speed
            'speechModel': 'experimental_conversations'  # Optimized for conversations
        }
    
    @classmethod
    def get_realtime_vad_config(cls) -> dict:
        """Get real-time VAD configuration for WebSocket streams"""
        return {
            'silence_threshold': 0.01,  # Low threshold for quick detection
            'silence_timeout_ms': cls.SILENCE_TIMEOUT,
            'speech_timeout_ms': cls.SPEECH_TIMEOUT,
            'min_speech_duration_ms': cls.MIN_SPEECH_LENGTH,
            'processing_delay_ms': cls.PROCESSING_DELAY
        }
    
    @classmethod
    def log_vad_performance(cls, silence_duration: float, speech_duration: float):
        """Log VAD performance metrics"""
        if silence_duration < cls.SILENCE_TIMEOUT / 1000:
            logger.info(f"🎯 VAD: Fast silence detection ({silence_duration:.3f}s)")
        else:
            logger.warning(f"⚠️ VAD: Slow silence detection ({silence_duration:.3f}s)")
        
        if speech_duration < 0.5:
            logger.info(f"🎯 VAD: Quick speech ({speech_duration:.3f}s)")
        elif speech_duration > 5.0:
            logger.warning(f"⚠️ VAD: Long speech ({speech_duration:.3f}s)")
            
# Global VAD configuration instance
vad_config = VADConfig()