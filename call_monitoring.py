"""
Real-time Call Monitoring System
Provides live call visibility, audio recording, and real-time transcription
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional
import requests
from flask_socketio import emit

logger = logging.getLogger(__name__)

class CallMonitor:
    """Manages real-time call monitoring, recording, and transcription"""
    
    def __init__(self):
        self.active_calls = {}  # call_sid -> call_info
        self.call_history = []  # Historical call records
        self.transcription_buffer = {}  # call_sid -> transcription_segments
        
    def start_call_monitoring(self, call_sid: str, from_number: str, to_number: str):
        """Start monitoring a new call"""
        call_info = {
            'call_sid': call_sid,
            'from_number': from_number,
            'to_number': to_number,
            'start_time': datetime.now().isoformat(),
            'status': 'in-progress',
            'duration': 0,
            'transcription': [],
            'recording_url': None,
            'caller_name': None,
            'issue_type': None,
            'resolution': None
        }
        
        self.active_calls[call_sid] = call_info
        logger.info(f"📞 Started monitoring call {call_sid} from {from_number}")
        
        # Emit to dashboard for real-time updates
        self._emit_call_update('call_started', call_info)
        
        return call_info
        
    def add_transcription_segment(self, call_sid: str, text: str, speaker: str = 'caller', timestamp: str = None):
        """Add real-time transcription segment"""
        if call_sid not in self.active_calls:
            return
            
        if not timestamp:
            timestamp = datetime.now().isoformat()
            
        segment = {
            'timestamp': timestamp,
            'speaker': speaker,
            'text': text,
            'duration_seconds': self._get_call_duration(call_sid)
        }
        
        self.active_calls[call_sid]['transcription'].append(segment)
        
        # Emit real-time transcription update
        self._emit_call_update('transcription_update', {
            'call_sid': call_sid,
            'segment': segment,
            'full_transcription': self.active_calls[call_sid]['transcription']
        })
        
        logger.info(f"📝 Added transcription for {call_sid}: {speaker} - {text[:50]}...")
        
    def update_call_info(self, call_sid: str, **kwargs):
        """Update call information (caller name, issue type, etc.)"""
        if call_sid not in self.active_calls:
            return
            
        for key, value in kwargs.items():
            if key in self.active_calls[call_sid]:
                self.active_calls[call_sid][key] = value
                
        # Emit update to dashboard
        self._emit_call_update('call_info_update', self.active_calls[call_sid])
        
    def set_recording_url(self, call_sid: str, recording_url: str):
        """Set the recording URL for a call"""
        if call_sid in self.active_calls:
            self.active_calls[call_sid]['recording_url'] = recording_url
            self._emit_call_update('recording_available', {
                'call_sid': call_sid,
                'recording_url': recording_url
            })
            
    def end_call_monitoring(self, call_sid: str, final_status: str = 'completed'):
        """End call monitoring and archive the call"""
        if call_sid not in self.active_calls:
            return
            
        call_info = self.active_calls[call_sid]
        call_info['end_time'] = datetime.now().isoformat()
        call_info['status'] = final_status
        call_info['duration'] = self._get_call_duration(call_sid)
        
        # Move to history
        self.call_history.append(call_info.copy())
        
        # Remove from active calls
        del self.active_calls[call_sid]
        
        # Emit final update
        self._emit_call_update('call_ended', call_info)
        
        logger.info(f"📞 Ended monitoring call {call_sid} - Duration: {call_info['duration']}s")
        
        return call_info
        
    def get_active_calls(self) -> List[Dict]:
        """Get all currently active calls"""
        # Update durations for active calls
        for call_sid, call_info in self.active_calls.items():
            call_info['duration'] = self._get_call_duration(call_sid)
            
        return list(self.active_calls.values())
        
    def get_call_history(self, limit: int = 50) -> List[Dict]:
        """Get recent call history"""
        return sorted(self.call_history, key=lambda x: x['start_time'], reverse=True)[:limit]
        
    def get_call_details(self, call_sid: str) -> Optional[Dict]:
        """Get detailed information about a specific call"""
        if call_sid in self.active_calls:
            call_info = self.active_calls[call_sid].copy()
            call_info['duration'] = self._get_call_duration(call_sid)
            return call_info
            
        # Search in history
        for call in self.call_history:
            if call['call_sid'] == call_sid:
                return call
                
        return None
        
    def search_calls(self, query: str = None, date_range: tuple = None) -> List[Dict]:
        """Search calls by various criteria"""
        all_calls = self.call_history + list(self.active_calls.values())
        
        if not query and not date_range:
            return all_calls
            
        filtered_calls = []
        
        for call in all_calls:
            match = True
            
            # Text search in transcription, caller name, issue type
            if query:
                search_text = query.lower()
                searchable_content = [
                    call.get('caller_name', ''),
                    call.get('issue_type', ''),
                    call.get('from_number', ''),
                    ' '.join([seg.get('text', '') for seg in call.get('transcription', [])])
                ]
                
                if not any(search_text in content.lower() for content in searchable_content):
                    match = False
                    
            # Date range filter
            if date_range and match:
                call_date = datetime.fromisoformat(call['start_time'].replace('Z', '+00:00'))
                if not (date_range[0] <= call_date <= date_range[1]):
                    match = False
                    
            if match:
                filtered_calls.append(call)
                
        return filtered_calls
        
    def _get_call_duration(self, call_sid: str) -> int:
        """Calculate call duration in seconds"""
        if call_sid not in self.active_calls:
            return 0
            
        start_time_str = self.active_calls[call_sid]['start_time']
        start_time = datetime.fromisoformat(start_time_str)
        return int((datetime.now() - start_time).total_seconds())
        
    def _emit_call_update(self, event_type: str, data: Dict):
        """Emit real-time updates to connected dashboards"""
        try:
            # This will be used by SocketIO for real-time updates
            # For now, we'll store updates for polling
            update = {
                'timestamp': datetime.now().isoformat(),
                'type': event_type,
                'data': data
            }
            
            # Could implement WebSocket emissions here
            logger.debug(f"🔄 Call update: {event_type} for {data.get('call_sid', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to emit call update: {e}")

# Global call monitor instance
call_monitor = CallMonitor()

def get_call_monitor():
    """Get the global call monitor instance"""
    return call_monitor

def start_call_monitoring(call_sid: str, from_number: str, to_number: str = None):
    """Convenience function to start monitoring a call"""
    return call_monitor.start_call_monitoring(call_sid, from_number, to_number or "+18886411102")

def add_call_transcription(call_sid: str, text: str, speaker: str = 'caller'):
    """Convenience function to add transcription"""
    return call_monitor.add_transcription_segment(call_sid, text, speaker)

def update_caller_info(call_sid: str, caller_name: str = None, issue_type: str = None):
    """Convenience function to update caller information"""
    updates = {}
    if caller_name:
        updates['caller_name'] = caller_name
    if issue_type:
        updates['issue_type'] = issue_type
    return call_monitor.update_call_info(call_sid, **updates)

def end_call_monitoring(call_sid: str, final_status: str = 'completed'):
    """Convenience function to end call monitoring"""
    return call_monitor.end_call_monitoring(call_sid, final_status)