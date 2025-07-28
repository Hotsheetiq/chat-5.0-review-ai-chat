"""
Enhanced Service Warm-up System with Monitoring
Keeps all external services active with status tracking and reliability features
"""

import threading
import time
import logging
import requests
import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class EnhancedServiceWarmup:
    def __init__(self):
        self.running = False
        self.threads = []
        
        # Service status tracking
        self.service_status = {
            'grok_ai': {
                'last_success': None,
                'last_error': None,
                'consecutive_failures': 0,
                'total_attempts': 0,
                'total_successes': 0,
                'is_healthy': False
            },
            'elevenlabs': {
                'last_success': None,
                'last_error': None,
                'consecutive_failures': 0,
                'total_attempts': 0,
                'total_successes': 0,
                'is_healthy': False
            },
            'twilio': {
                'last_success': None,
                'last_error': None,
                'consecutive_failures': 0,
                'total_attempts': 0,
                'total_successes': 0,
                'is_healthy': False
            },
            'rent_manager': {
                'last_success': None,
                'last_error': None,
                'consecutive_failures': 0,
                'total_attempts': 0,
                'total_successes': 0,
                'is_healthy': False,
                'token_refreshed': None
            }
        }
        
        # Warm-up intervals (seconds)
        self.intervals = {
            'grok_ai': 600,        # 10 minutes
            'elevenlabs': 600,     # 10 minutes
            'twilio': 300,         # 5 minutes
            'rent_manager': 600    # 10 minutes
        }
        
        # Failure threshold for alerts
        self.failure_threshold = 3
        
    def start_warmup_system(self):
        """Start all enhanced warm-up threads"""
        if self.running:
            logger.info("🔥 Warm-up system already running")
            return
            
        self.running = True
        logger.info("🔥 Starting enhanced service warm-up system...")
        
        # Start individual warm-up threads
        warmup_services = [
            ('grok_ai', self._warmup_grok_ai),
            ('elevenlabs', self._warmup_elevenlabs),
            ('twilio', self._warmup_twilio),
            ('rent_manager', self._warmup_rent_manager)
        ]
        
        for service_name, warmup_func in warmup_services:
            thread = threading.Thread(
                target=self._run_warmup_loop, 
                args=(service_name, warmup_func), 
                daemon=True
            )
            thread.start()
            self.threads.append(thread)
            
        logger.info("✅ All enhanced warm-up threads started")
        
    def stop_warmup_system(self):
        """Stop all warm-up threads"""
        self.running = False
        logger.info("🛑 Stopping enhanced service warm-up system...")
        
    def _run_warmup_loop(self, service_name: str, warmup_function):
        """Run a warm-up function with status tracking"""
        interval = self.intervals[service_name]
        
        while self.running:
            try:
                success = warmup_function()
                self._update_service_status(service_name, success)
                
            except Exception as e:
                logger.error(f"❌ {service_name} warm-up error: {e}")
                self._update_service_status(service_name, False, str(e))
                
            # Wait for next warm-up cycle
            time.sleep(interval)
            
    def _update_service_status(self, service_name: str, success: bool, error_msg: str = None):
        """Update service status tracking"""
        status = self.service_status[service_name]
        status['total_attempts'] += 1
        
        if success:
            status['last_success'] = datetime.now()
            status['consecutive_failures'] = 0
            status['total_successes'] += 1
            status['is_healthy'] = True
            status['last_error'] = None
            logger.info(f"✅ {service_name} warm-up successful")
        else:
            status['consecutive_failures'] += 1
            status['last_error'] = error_msg or "Unknown error"
            status['is_healthy'] = status['consecutive_failures'] < self.failure_threshold
            
            # Log warnings for consecutive failures
            if status['consecutive_failures'] >= self.failure_threshold:
                logger.warning(f"⚠️ {service_name} has {status['consecutive_failures']} consecutive failures - needs manual review")
            
            logger.error(f"❌ {service_name} warm-up failed: {error_msg}")
    
    def _warmup_grok_ai(self) -> bool:
        """Warm up Grok AI with a test request"""
        try:
            from grok_integration import GrokAI
            
            # Use the same Grok AI instance from main app
            grok_ai = GrokAI()
            
            # Send a minimal warm-up request with proper message format
            test_messages = [{"role": "user", "content": "Hello"}]
            response = grok_ai.generate_response(
                test_messages,
                max_tokens=10,
                timeout=5.0
            )
            
            if response and len(response) > 0:
                logger.info("🚀 Grok AI pre-warmed successfully")
                return True
            else:
                logger.warning("⚠️ Grok AI returned empty response")
                return False
                
        except Exception as e:
            logger.error(f"❌ Grok AI warm-up failed: {e}")
            return False
    
    def _warmup_elevenlabs(self) -> bool:
        """Warm up ElevenLabs with correct voice model"""
        try:
            ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
            if not ELEVENLABS_API_KEY:
                logger.error("❌ ElevenLabs API key not found")
                return False
            
            # Use the same voice ID and model as production
            CHRIS_VOICE_ID = "f218e5pATi8cBqEEIGBU"  # Chris's production voice
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{CHRIS_VOICE_ID}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": ELEVENLABS_API_KEY
            }
            
            # Warm-up with minimal text using production settings
            data = {
                "text": "warm-up test",
                "model_id": "eleven_turbo_v2_5",  # Production model
                "voice_settings": {
                    "stability": 0.15,
                    "similarity_boost": 0.85,
                    "style": 0.2,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                logger.info("🚀 ElevenLabs voice model pre-warmed successfully")
                return True
            else:
                logger.error(f"❌ ElevenLabs warm-up failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ ElevenLabs warm-up error: {e}")
            return False
    
    def _warmup_twilio(self) -> bool:
        """Warm up Twilio webhook endpoint"""
        try:
            # Get the correct Replit URL
            base_url = os.environ.get('REPLIT_URL', 'https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev')
            
            # Ping the main webhook endpoint
            response = requests.get(f"{base_url}/", timeout=10)
            
            if response.status_code == 200:
                logger.info("🚀 Twilio webhook endpoint pre-warmed successfully")
                return True
            else:
                logger.error(f"❌ Twilio webhook warm-up failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Twilio webhook warm-up error: {e}")
            return False
    
    def _warmup_rent_manager(self) -> bool:
        """Warm up Rent Manager API with token validation"""
        try:
            from rent_manager import RentManagerAPI
            
            # Initialize Rent Manager API
            rent_manager_username = os.environ.get('RENT_MANAGER_USERNAME', '')
            rent_manager_password = os.environ.get('RENT_MANAGER_PASSWORD', '')
            rent_manager_location = os.environ.get('RENT_MANAGER_LOCATION_ID', '1')
            
            if not all([rent_manager_username, rent_manager_password]):
                logger.error("❌ Rent Manager credentials not found")
                return False
            
            credentials_string = f"{rent_manager_username}:{rent_manager_password}:{rent_manager_location}"
            rent_manager = RentManagerAPI(credentials_string)
            
            # Test authentication directly since it's the most reliable check
            try:
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Simple authentication test
                result = loop.run_until_complete(asyncio.wait_for(
                    rent_manager.authenticate(),
                    timeout=10.0
                ))
                
                if result and rent_manager.session_token:
                    # Test with a simple API call to verify token works
                    properties = loop.run_until_complete(asyncio.wait_for(
                        rent_manager.get_all_properties(),
                        timeout=10.0
                    ))
                    loop.close()
                    
                    if properties is not None:  # Even empty list is success
                        logger.info("🚀 Rent Manager API authenticated and tested successfully")
                        return True
                    else:
                        logger.warning("⚠️ Rent Manager authentication succeeded but API test failed")
                        return False
                else:
                    loop.close()
                    logger.error("❌ Rent Manager authentication failed")
                    return False
                    
            except Exception as auth_error:
                logger.error(f"❌ Rent Manager authentication error: {auth_error}")
                return False
                # No token, authenticate fresh
                logger.info("🔄 Rent Manager authenticating fresh token...")
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                success = loop.run_until_complete(asyncio.wait_for(
                    rent_manager.authenticate(),
                    timeout=15.0
                ))
                loop.close()
                
                if success:
                    logger.info("🚀 Rent Manager API authenticated successfully")
                    return True
                else:
                    logger.error("❌ Rent Manager authentication failed")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Rent Manager warm-up error: {e}")
            return False
    
    def _refresh_rent_manager_token(self, rent_manager) -> bool:
        """Attempt to refresh Rent Manager token"""
        try:
            import asyncio
            
            # Force re-authentication
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            success = loop.run_until_complete(asyncio.wait_for(
                rent_manager.authenticate(),
                timeout=15.0
            ))
            loop.close()
            
            if success:
                self.service_status['rent_manager']['token_refreshed'] = datetime.now()
                logger.info("✅ Rent Manager token refreshed successfully")
                return True
            else:
                logger.error("❌ Rent Manager token refresh failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Rent Manager token refresh error: {e}")
            return False
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get comprehensive status summary for monitoring dashboard"""
        # Use Eastern Time for dashboard display
        import pytz
        eastern = pytz.timezone('US/Eastern')
        eastern_now = datetime.now(eastern)
        
        summary = {
            'system_status': 'healthy' if self.running else 'stopped',
            'last_updated': eastern_now,
            'services': {}
        }
        
        for service_name, status in self.service_status.items():
            # Convert last_success to Eastern Time if it exists
            last_success_et = None
            if status['last_success']:
                import pytz
                eastern = pytz.timezone('US/Eastern')
                if status['last_success'].tzinfo is None:
                    # Assume UTC if no timezone info
                    utc_time = pytz.utc.localize(status['last_success'])
                    last_success_et = utc_time.astimezone(eastern)
                else:
                    last_success_et = status['last_success'].astimezone(eastern)
            
            # Fix health status - if no successes and has failures, mark as unhealthy
            actual_is_healthy = (
                status['is_healthy'] and 
                status['total_successes'] > 0 and 
                status['consecutive_failures'] < self.failure_threshold
            )
            
            service_summary = {
                'is_healthy': actual_is_healthy,
                'last_success': last_success_et,  # Eastern Time for template
                'last_error': status['last_error'],
                'consecutive_failures': status['consecutive_failures'],
                'success_rate': round((status['total_successes'] / max(status['total_attempts'], 1)) * 100, 1),
                'needs_attention': (status['consecutive_failures'] >= self.failure_threshold) or (status['total_successes'] == 0 and status['total_attempts'] > 0)
            }
            
            # Add special fields for rent manager - convert to Eastern Time
            if service_name == 'rent_manager' and status.get('token_refreshed'):
                token_refreshed_et = None
                if status['token_refreshed']:
                    import pytz
                    eastern = pytz.timezone('US/Eastern')
                    if status['token_refreshed'].tzinfo is None:
                        utc_time = pytz.utc.localize(status['token_refreshed'])
                        token_refreshed_et = utc_time.astimezone(eastern)
                    else:
                        token_refreshed_et = status['token_refreshed'].astimezone(eastern)
                service_summary['token_refreshed'] = token_refreshed_et
            
            summary['services'][service_name] = service_summary
        
        return summary

# Global warmup instance
enhanced_warmup = EnhancedServiceWarmup()

def start_enhanced_warmup():
    """Start the enhanced warm-up system"""
    enhanced_warmup.start_warmup_system()

def stop_enhanced_warmup():
    """Stop the enhanced warm-up system"""
    enhanced_warmup.stop_warmup_system()

def get_warmup_status():
    """Get the current warm-up status"""
    return enhanced_warmup.get_status_summary()