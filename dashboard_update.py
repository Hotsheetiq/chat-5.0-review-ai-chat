"""
Dashboard updates to show OpenAI real-time system status
Maintains existing dashboard functionality while adding new voice modes
"""

def add_openai_status_to_dashboard_template():
    """Add OpenAI status indicators to existing dashboard template"""
    
    dashboard_additions = """
    <!-- OpenAI Real-time Status Section -->
    <div class="col-md-6 mb-4">
        <div class="card border-success">
            <div class="card-body">
                <h5 class="card-title">
                    <i class="fas fa-microphone text-success"></i>
                    OpenAI Voice Assistant
                </h5>
                <div class="row">
                    <div class="col-6">
                        <div class="status-indicator">
                            <span class="status-dot" id="openai-status"></span>
                            <span id="openai-text">Checking...</span>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="status-indicator">
                            <span class="status-dot" id="mode-status"></span>
                            <span id="mode-text">Default Mode</span>
                        </div>
                    </div>
                </div>
                <div class="mt-3">
                    <label for="voice-mode-select" class="form-label">Voice Mode:</label>
                    <select class="form-select" id="voice-mode-select" onchange="changeVoiceMode()">
                        <option value="default" selected>Default - STT→OpenAI→TTS</option>
                        <option value="live">Live - Realtime API + VAD</option>
                        <option value="reasoning">Reasoning - Heavy thinking</option>
                    </select>
                </div>
                <div class="mt-2">
                    <small class="text-muted">
                        <strong>Current:</strong> <span id="mode-description">Fast streaming with gpt-4o-mini</span>
                    </small>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Voice Activity Detection Status -->
    <div class="col-md-6 mb-4">
        <div class="card border-info">
            <div class="card-body">
                <h5 class="card-title">
                    <i class="fas fa-volume-up text-info"></i>
                    Voice Activity Detection
                </h5>
                <div class="row">
                    <div class="col-6">
                        <div class="status-indicator">
                            <span class="status-dot" id="vad-status"></span>
                            <span id="vad-text">Ready</span>
                        </div>
                    </div>
                    <div class="col-6">
                        <div class="status-indicator">
                            <span class="status-dot" id="streaming-status"></span>
                            <span id="streaming-text">Idle</span>
                        </div>
                    </div>
                </div>
                <div class="mt-3">
                    <div class="progress">
                        <div class="progress-bar" id="audio-level" style="width: 0%"></div>
                    </div>
                    <small class="text-muted">Audio Level</small>
                </div>
            </div>
        </div>
    </div>
    """
    
    dashboard_javascript = """
    // OpenAI Voice Assistant Status Monitoring
    let currentVoiceMode = 'default';
    
    function updateVoiceStatus() {
        fetch('/voice-status')
            .then(response => response.json())
            .then(data => {
                const openaiStatus = document.getElementById('openai-status');
                const openaiText = document.getElementById('openai-text');
                const modeStatus = document.getElementById('mode-status');
                const modeText = document.getElementById('mode-text');
                
                if (data.system_ready) {
                    openaiStatus.className = 'status-dot status-active';
                    openaiText.textContent = 'Connected';
                } else {
                    openaiStatus.className = 'status-dot status-error';
                    openaiText.textContent = 'Disconnected';
                }
                
                // Update mode status
                currentVoiceMode = data.openai_status.current_mode;
                modeStatus.className = 'status-dot status-active';
                modeText.textContent = currentVoiceMode.charAt(0).toUpperCase() + currentVoiceMode.slice(1);
                
                // Update mode description
                const descriptions = {
                    'default': 'Fast streaming with gpt-4o-mini',
                    'live': 'Realtime API with voice activity detection',
                    'reasoning': 'Heavy thinking with gpt-4.1/gpt-5.0'
                };
                
                document.getElementById('mode-description').textContent = descriptions[currentVoiceMode];
                
                // Update VAD status
                const vadStatus = document.getElementById('vad-status');
                const vadText = document.getElementById('vad-text');
                
                if (data.vad_status && data.vad_status.is_speaking) {
                    vadStatus.className = 'status-dot status-warning';
                    vadText.textContent = 'Speaking';
                } else {
                    vadStatus.className = 'status-dot status-active';
                    vadText.textContent = 'Listening';
                }
            })
            .catch(error => {
                console.error('Voice status check failed:', error);
                document.getElementById('openai-status').className = 'status-dot status-error';
                document.getElementById('openai-text').textContent = 'Error';
            });
    }
    
    function changeVoiceMode() {
        const select = document.getElementById('voice-mode-select');
        const newMode = select.value;
        
        fetch(`/voice-mode/${newMode}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentVoiceMode = newMode;
                    showAlert(`Voice mode switched to ${newMode}`, 'success');
                    updateVoiceStatus();
                } else {
                    showAlert('Failed to switch voice mode', 'error');
                }
            })
            .catch(error => {
                console.error('Mode switch failed:', error);
                showAlert('Error switching voice mode', 'error');
            });
    }
    
    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : 'success'} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container-fluid').prepend(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
    
    // Update voice status every 5 seconds
    setInterval(updateVoiceStatus, 5000);
    updateVoiceStatus(); // Initial check
    """
    
    return dashboard_additions, dashboard_javascript

def get_openai_dashboard_data():
    """Get dashboard data for OpenAI system status"""
    from openai_realtime_integration import openai_assistant
    from voice_activity_detection import vad_detector
    
    try:
        openai_status = openai_assistant.get_system_status()
        vad_status = vad_detector.get_status()
        
        return {
            "openai_connected": openai_status["openai_connected"],
            "current_mode": openai_status["current_mode"],
            "realtime_active": openai_status["realtime_active"],
            "processing": openai_status["processing"],
            "vad_active": vad_status["is_speaking"],
            "models": openai_status["models"]
        }
    except Exception as e:
        return {
            "openai_connected": False,
            "current_mode": "unknown",
            "realtime_active": False,
            "processing": False,
            "vad_active": False,
            "models": {},
            "error": str(e)
        }