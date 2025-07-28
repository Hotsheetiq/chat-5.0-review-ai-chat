"""
Automated Service Warm-Up System
Reduces cold start latency by keeping all integrated services active
"""

import os
import time
import threading
import logging
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ServiceWarmup:
    def __init__(self):
        self.running = False
        self.threads = []
        # Get correct Replit URL
        repl_slug = os.environ.get('REPL_SLUG', '')
        if repl_slug and repl_slug != 'workspace':
            self.base_url = f"https://{repl_slug}"
        else:
            # Use the direct Replit domain format
            self.base_url = "https://3442ef02-e255-4239-86b6-df0f7a6e4975-00-1w63nn4pu7btq.picard.replit.dev"
        
        # Warm-up intervals (seconds)
        self.intervals = {
            'twilio_webhook': 300,    # 5 minutes
            'replit_backend': 300,    # 5 minutes
            'grok_ai': 600,          # 10 minutes
            'elevenlabs': 600,       # 10 minutes
            'rent_manager': 600      # 10 minutes
        }
        
        # Last successful warm-up times
        self.last_warmup = {}
        
    def start_warmup_system(self):
        """Start all warm-up threads"""
        if self.running:
            return
            
        self.running = True
        logger.info("🔥 Starting service warm-up system...")
        
        # Start individual warm-up threads
        warmup_functions = [
            self._warmup_twilio_webhook,
            self._warmup_replit_backend,
            self._warmup_grok_ai,
            self._warmup_elevenlabs,
            self._warmup_rent_manager
        ]
        
        for func in warmup_functions:
            thread = threading.Thread(target=self._run_warmup_loop, args=(func,), daemon=True)
            thread.start()
            self.threads.append(thread)
            
        logger.info("✅ All warm-up threads started")
        
    def stop_warmup_system(self):
        """Stop all warm-up threads"""
        self.running = False
        logger.info("🛑 Stopping service warm-up system...")
        
    def _run_warmup_loop(self, warmup_function):
        """Run a warm-up function in a loop"""
        while self.running:
            try:
                warmup_function()
            except Exception as e:
                logger.error(f"❌ Warm-up error in {warmup_function.__name__}: {e}")
            
            # Sleep for the appropriate interval
            time.sleep(60)  # Check every minute, but respect individual intervals
            
    def _should_warmup(self, service_name: str) -> bool:
        """Check if a service needs warm-up based on interval"""
        last_time = self.last_warmup.get(service_name, 0)
        interval = self.intervals.get(service_name, 300)
        return time.time() - last_time >= interval
        
    def _record_warmup(self, service_name: str):
        """Record successful warm-up time"""
        self.last_warmup[service_name] = time.time()
        
    def _warmup_twilio_webhook(self):
        """Warm up Twilio webhook endpoints"""
        if not self._should_warmup('twilio_webhook'):
            return
            
        try:
            # Ping main webhook endpoint - this keeps the route active
            response = requests.get(
                f"{self.base_url}/dashboard", 
                timeout=10,
                headers={'User-Agent': 'ServiceWarmup/1.0'}
            )
            
            # 200 is good, 404 means route exists but endpoint doesn't match (still keeps warm)
            if response.status_code in [200, 404]:
                self._record_warmup('twilio_webhook')
                logger.debug("🔥 Twilio webhook warmed up")
            else:
                logger.warning(f"⚠️  Twilio webhook warm-up returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Twilio webhook warm-up failed: {e}")
            
    def _warmup_replit_backend(self):
        """Warm up Replit backend routes"""
        if not self._should_warmup('replit_backend'):
            return
            
        try:
            # Ping key backend routes
            routes_to_ping = [
                '/dashboard',
                '/admin-training',
                '/status'
            ]
            
            for route in routes_to_ping:
                try:
                    response = requests.get(
                        f"{self.base_url}{route}",
                        timeout=5,
                        headers={'User-Agent': 'ServiceWarmup/1.0'}
                    )
                    
                    if response.status_code in [200, 404]:  # 404 is okay, means route exists
                        continue
                    else:
                        logger.warning(f"⚠️  Backend route {route} returned {response.status_code}")
                        
                except requests.exceptions.RequestException:
                    continue  # Skip failed routes
                    
            self._record_warmup('replit_backend')
            logger.debug("🔥 Replit backend warmed up")
            
        except Exception as e:
            logger.error(f"❌ Replit backend warm-up failed: {e}")
            
    def _warmup_grok_ai(self):
        """Warm up Grok AI model"""
        if not self._should_warmup('grok_ai'):
            return
            
        try:
            from grok_integration import GrokAI
            
            # Initialize Grok if not already done
            grok = GrokAI()
            
            # Send properly formatted warm-up message
            response = grok.generate_response(
                [{"role": "user", "content": "hello"}],
                max_tokens=5,
                temperature=0.1
            )
            
            if response:
                self._record_warmup('grok_ai')
                logger.debug("🔥 Grok AI warmed up")
            else:
                logger.warning("⚠️  Grok AI warm-up returned empty response")
                
        except Exception as e:
            logger.error(f"❌ Grok AI warm-up failed: {e}")
            
    def _warmup_elevenlabs(self):
        """Warm up ElevenLabs TTS"""
        if not self._should_warmup('elevenlabs'):
            return
            
        try:
            import requests
            
            # Direct ElevenLabs API call for warm-up
            api_key = os.environ.get('ELEVENLABS_API_KEY')
            if not api_key:
                logger.warning("⚠️  ElevenLabs API key not found")
                return
                
            url = f"https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": api_key
            }
            data = {
                "text": "check",
                "model_id": "eleven_turbo_v2_5",
                "voice_settings": {
                    "stability": 0.15,
                    "similarity_boost": 0.85,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                self._record_warmup('elevenlabs')
                logger.debug("🔥 ElevenLabs TTS warmed up")
            else:
                logger.warning(f"⚠️  ElevenLabs warm-up returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ ElevenLabs warm-up failed: {e}")
            
    def _warmup_rent_manager(self):
        """Warm up Rent Manager API"""
        if not self._should_warmup('rent_manager'):
            return
            
        try:
            import requests
            
            # Get credentials from environment
            api_key = os.environ.get('RENT_MANAGER_API_KEY')
            username = os.environ.get('RENT_MANAGER_USERNAME') 
            password = os.environ.get('RENT_MANAGER_PASSWORD')
            location_id = os.environ.get('RENT_MANAGER_LOCATION_ID')
            
            if not all([api_key, username, password, location_id]):
                logger.warning("⚠️  Rent Manager credentials not complete")
                return
                
            # Authenticate and get token
            auth_url = "https://grinb.api.rentmanager.com/Authentication/AuthorizeUser"
            auth_data = {
                "Username": username,
                "Password": password,
                "LocationID": int(location_id)
            }
            
            response = requests.post(
                auth_url, 
                json=auth_data,
                headers={
                    "X-RM12Api-ApiToken": api_key,
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            # 200 is success, 401 means we're hitting the API (keeps connection warm)
            if response.status_code in [200, 401]:
                self._record_warmup('rent_manager')
                logger.debug("🔥 Rent Manager API warmed up")
            else:
                logger.warning(f"⚠️  Rent Manager warm-up returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Rent Manager warm-up failed: {e}")
            
    def get_warmup_status(self) -> Dict[str, Any]:
        """Get current warm-up status for all services"""
        current_time = time.time()
        status = {}
        
        for service, interval in self.intervals.items():
            last_warmup = self.last_warmup.get(service, 0)
            next_warmup = last_warmup + interval
            
            status[service] = {
                'last_warmup': datetime.fromtimestamp(last_warmup).isoformat() if last_warmup else None,
                'next_warmup': datetime.fromtimestamp(next_warmup).isoformat(),
                'interval_minutes': interval // 60,
                'status': 'active' if current_time - last_warmup < interval * 1.5 else 'stale'
            }
            
        return status

# Global warm-up instance
warmup_system = None

def initialize_warmup_system():
    """Initialize and start the warm-up system"""
    global warmup_system
    
    if warmup_system is None:
        warmup_system = ServiceWarmup()
        warmup_system.start_warmup_system()
        logger.info("🔥 Service warm-up system initialized")
    
    return warmup_system

def get_warmup_status():
    """Get warm-up system status"""
    if warmup_system:
        return warmup_system.get_warmup_status()
    return {}

def stop_warmup_system():
    """Stop the warm-up system"""
    global warmup_system
    
    if warmup_system:
        warmup_system.stop_warmup_system()
        warmup_system = None
        logger.info("🛑 Service warm-up system stopped")