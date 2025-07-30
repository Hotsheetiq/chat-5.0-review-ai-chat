# Logging Rules

1. Never overwrite or delete logs from the Request History dashboard.
2. Only append new entries or update the resolution of a specific log (e.g., log #007).
3. Never modify or remove the original request text unless explicitly instructed.
4. Always mirror each log update to the file REQUEST_HISTORY.md.
5. Logs should be ordered from newest to oldest in the dashboard view.

## 🛡️ AUTOMATIC CALL LOGGING SYSTEM PROTECTION - Added: July 30, 2025 at 2:48 PM ET

**CRITICAL CONSTRAINT**: The automatic logging system that connects live call processing to logs_persistent.json MUST NEVER be disabled, removed, or modified.

### Protected Components:
1. **Auto-logging Integration**: Lines 1871-1885 in fixed_conversation_app.py - automatic call interaction logging
2. **Call Type Detection**: Intelligent categorization system (maintenance vs general calls)
3. **Silent Operation**: Error-only logging to prevent console spam during normal operation
4. **Persistent Storage**: Real-time updates to logs_persistent.json for every call interaction
5. **Automatic Timestamping**: Eastern Time integration with proper formatting

### Protected Functions:
- Auto-logging code block in handle_speech function that triggers on speech_result > 2 characters
- auto_log_request() function calls with live call data
- Call type detection logic using keyword matching
- Persistent storage integration that saves logs automatically

### User Confirmation:
User explicitly requested "add this fix to constraint rule" after confirming the automatic logging system works perfectly.

### Rationale:
This logging system provides critical visibility into live call operations at (888) 641-1102. Every call interaction is automatically tracked without manual intervention, ensuring complete operational transparency.

**ABSOLUTE PROTECTION**: Any attempt to disable, modify, or remove the automatic logging integration is STRICTLY PROHIBITED.

## 🛡️ PROGRAMMING LOG RESTORATION SYSTEM PROTECTION - Added: July 30, 2025 at 3:38 PM ET

**CRITICAL CONSTRAINT**: The programming repair log restoration and separation system MUST NEVER be disabled, removed, or modified.

### Protected Components:
1. **Log Classification System**: Clear distinction between 📞 LIVE CALL logs and programming fix requests
2. **Programming Log Restoration**: Process for recovering legitimate development work logs when accidentally removed
3. **Log Separation Logic**: Automated system that distinguishes call interactions from programming requests
4. **Complete Development Tracking**: All legitimate programming repair work must be maintained in logs_persistent.json

### Protected Functionality:
- Programming repair log identification and restoration process
- Call log vs programming log classification system
- Development work tracking and documentation system
- Log numbering sequence maintenance for programming fixes

### User Confirmation:
User explicitly requested "lets add this fix to constraint rules" after confirming the programming log restoration system works correctly.

### Rationale:
This system ensures complete visibility into all legitimate programming repair work while properly separating operational call data from development tracking. Critical for maintaining comprehensive development history and preventing accidental loss of programming fix documentation.

**ABSOLUTE PROTECTION**: Any attempt to disable, modify, or remove the programming log restoration and separation system is STRICTLY PROHIBITED.

## CRITICAL PROTECTION: AUTOMATIC LOGGING SYSTEM (ABSOLUTE CONSTRAINT)

**AUTOMATIC REQUEST LOGGING SYSTEM - DO NOT REMOVE OR DISABLE**

The following automatic logging components are CRITICAL and must NEVER be removed or disabled:

### Protected Functions:
- `auto_log_request()` - automatically captures user requests and creates log entries
- `load_logs_from_file()` - loads persistent logs from JSON storage
- `save_logs_to_file()` - saves logs to persistent JSON storage
- `append_new_log()` - adds new log entries with persistence

### Protected API Endpoint:
- `/api/auto-log-request` - enables automatic logging via HTTP POST requests

### Protected Files:
- `logs_persistent.json` - maintains log persistence across server restarts

### Protected Features:
- Sequential ID generation system (ensures proper log numbering)
- Eastern Time timestamp integration (accurate time tracking)
- Persistent JSON storage (survives server restarts)
- Automatic constraint note addition (rule compliance documentation)

**JUSTIFICATION**: User confirmed "This fix works — create a necessary constraint so it's not undone in the future"

**VIOLATION WARNING**: Removing or disabling automatic logging breaks the user's request tracking workflow and violates established user requirements.

## 🛡️ GROK API RESPONSE PARSING PROTECTION - Added: July 29, 2025 at 4:37 AM ET

**CRITICAL CONSTRAINT**: The Grok API response parsing fix must be permanently protected from removal or modification.

### Protected Components:
1. **Enhanced Grok 2 Fallback System**: When Grok 4.0 returns empty responses, system MUST fallback to Grok 2 (grok-2-1212) model
2. **Comprehensive Debug Logging**: Full prompt logging, response object inspection, and controlled testing must remain active
3. **Error Handling for Empty Responses**: KeyError, IndexError, and AttributeError handling with detailed debug information
4. **Intelligent Contextual Responses**: Smart fallback responses based on user input keywords (heating, electrical, plumbing, pest, etc.)
5. **Complaint Confirmation Integration**: Enhanced responses include complaint confirmation phrases like "Let me make sure I understand..." and "Did I get that right?"

### Technical Implementation Protection:
- `grok_integration.py` - Enhanced fallback system with Grok 2 for empty Grok 4.0 responses
- Response parsing with comprehensive error handling and debug logging
- Contextual intelligent responses when both models fail
- Complaint confirmation phrases integrated into fallback responses

### Reason for Protection:
Root cause identified: Grok 4.0 consistently returns empty responses despite successful HTTP 200 API calls. Grok 2 works perfectly and provides detailed, helpful responses. This fix ensures Chris reliably understands all tenant issues and complaints.

**ABSOLUTE PROTECTION**: This parsing fix resolves the critical issue where "chris cant understan my issue" - removing or modifying this system will break Chris's ability to understand tenant complaints and issues.

## CRITICAL PROTECTION: DUPLICATE EMAIL PREVENTION SYSTEM (ABSOLUTE CONSTRAINT - Added: July 29, 2025 at 11:57 PM ET)

**DUPLICATE EMAIL PREVENTION SYSTEM - DO NOT REMOVE OR DISABLE**

The following email system components are CRITICAL and must NEVER be removed or disabled:

### Protected Variables:
- `email_sent_calls = set()` - Global tracker preventing duplicate emails per call_sid - PROTECTED
- Must remain at module level in fixed_conversation_app.py - PROTECTED

### Protected Logic:
- `if call_sid not in email_sent_calls:` - Duplicate prevention check before ALL email sends - PROTECTED
- `email_sent_calls.add(call_sid)` - Call tracking after successful email delivery - PROTECTED
- All email triggers must check tracker before sending - PROTECTED

### Protected Email Triggers:
- AI promise fulfillment email trigger with duplicate prevention - PROTECTED
- Pest control email triggers with duplicate prevention - PROTECTED  
- Fallback email trigger with duplicate prevention - PROTECTED
- All email triggers must use the tracker system - PROTECTED

### Protected Functionality:
- Single email guarantee: Exactly ONE email per call regardless of trigger count - PROTECTED
- Email tracking across all conversation paths and AI responses - PROTECTED
- Prevention of multiple transcript emails for same call_sid - PROTECTED

**JUSTIFICATION**: User confirmed "email fix works - create a necessary constraint so it's not undone in the future"

**VIOLATION WARNING**: Removing email_sent_calls tracker or disabling duplicate prevention will cause multiple emails per call, creating unprofessional spam and violating user requirements.

## CRITICAL PROTECTION: COMPLAINT CONFIRMATION SYSTEM (ABSOLUTE CONSTRAINT - Added: July 29, 2025 at 11:23 PM ET)

**COMPLAINT CONFIRMATION PROTOCOL - DO NOT REMOVE OR DISABLE**

The following complaint confirmation components are CRITICAL and must NEVER be removed or disabled:

### Protected AI System Prompt Rules:
- "CRITICAL COMPLAINT CONFIRMATION PROTOCOL" section in AI system prompt - PROTECTED
- Complaint repeat-back requirement for tenant issues/concerns/problems - PROTECTED
- Confirmation phrases: "Let me make sure I understand...", "So you're saying...", "Just to confirm..." - PROTECTED
- Summary requirement: "Summarize their issue in your own words to show you heard them correctly" - PROTECTED
- Confirmation verification: "Did I get that right?" or "Is that correct?" - PROTECTED

### Protected Conversation Flow:
- Step 1: REPEAT BACK tenant complaint to confirm understanding - PROTECTED
- Step 2: Summarize issue in Chris's own words - PROTECTED  
- Step 3: Ask for confirmation before proceeding - PROTECTED
- Step 4: Only proceed with solution AFTER tenant confirms - PROTECTED

### Protected Examples:
- Heat issue example: "Let me make sure I understand - you're saying the heating in your unit isn't working properly. Is that correct?" - PROTECTED
- Roach issue example: "So you're telling me there's a roach problem in your apartment. Did I get that right?" - PROTECTED

### Protected Functionality:
- Chris must demonstrate active listening by repeating complaints back - PROTECTED
- Prevents misunderstandings by confirming what tenant actually said - PROTECTED
- Builds trust through acknowledgment before moving to solutions - PROTECTED
- Ensures accurate problem documentation for service tickets - PROTECTED

**JUSTIFICATION**: User requested "Add complaint confirmation - Chris should repeat back complaints to confirm understanding before proceeding"

**VIOLATION WARNING**: Removing complaint confirmation protocol will cause Chris to skip acknowledgment of tenant concerns, leading to misunderstandings and poor customer service experience.

## CRITICAL PROTECTION: ANTI-REPETITION SYSTEM (ABSOLUTE CONSTRAINT - Added: July 29, 2025 at 12:05 AM ET)

**ANTI-REPETITION SYSTEM - DO NOT REMOVE OR DISABLE**

The following anti-repetition components are CRITICAL and must NEVER be removed or disabled:

### Protected Variables:
- `response_tracker = {}` - Global tracker preventing exact phrase repetition per call_sid - PROTECTED
- Must remain at module level in fixed_conversation_app.py - PROTECTED

### Protected Logic:
- `if call_sid not in response_tracker: response_tracker[call_sid] = set()` - Per-call tracking initialization - PROTECTED
- `response_tracker[call_sid].add(response_text)` - Response recording after each Chris message - PROTECTED
- AI repetition detection: `if response_text in response_tracker[call_sid]:` - PROTECTED

### Protected Features:
- Varied clarification options array with 5 different phrases - PROTECTED
- AI system prompt anti-repetition warning - PROTECTED
- Response filtering to use unused clarification phrases - PROTECTED
- Automatic tracker reset when all options exhausted - PROTECTED

### Protected AI Integration:
- AI repetition detection with varied response regeneration - PROTECTED
- Temperature increase (0.8) for varied responses when repetition detected - PROTECTED
- Response tracking integration with conversation history storage - PROTECTED

**JUSTIFICATION**: User reported "chris asks mutiple time for clarification" and requested "create a rule that he is not allowed to repeat himself using exact the same phrase"

**VIOLATION WARNING**: Removing response_tracker or disabling anti-repetition will cause Chris to repeat identical clarification phrases, creating poor user experience and violating conversation intelligence requirements.

## CRITICAL PROTECTION: GROK 4.0 PRIMARY MODEL (ABSOLUTE CONSTRAINT - Added: July 29, 2025 at 12:17 AM ET)

**GROK 4.0 PRIMARY MODEL - MUST ALWAYS BE USED**

The following Grok 4.0 AI model components are CRITICAL and must NEVER be changed:

### Protected Model Selection:
- `model="grok-4-0709"` - MUST ALWAYS be primary AI model for Chris intelligence - PROTECTED
- Grok 4.0 must be first choice for all conversation processing - PROTECTED
- Only Grok 2 as emergency fallback for API connection errors (not empty responses) - PROTECTED

### Protected Components:
- Primary model selection in `grok_integration.py` - PROTECTED
- All AI conversation processing must use Grok 4.0 first - PROTECTED
- Response generation for Chris's intelligence - PROTECTED
- Conversation understanding and context processing - PROTECTED

### Protected Logic:
- Grok 4.0 must be attempted first for all AI requests - PROTECTED
- Enhanced debugging for empty responses from Grok 4.0 - PROTECTED
- Intelligent fallback responses for empty Grok 4.0 responses - PROTECTED
- Never switch primary model away from Grok 4.0 - PROTECTED

**JUSTIFICATION**: User explicitly required "i want grock.40 to always be used so add that to the constraint"

**VIOLATION WARNING**: Switching primary AI model away from Grok 4.0 violates direct user requirement and degrades conversation intelligence quality.

Before updating the UI or any logs, read this file and confirm you're following the rules.

## CRITICAL SYSTEM PROTECTION - AI RESPONSE INTEGRITY (ABSOLUTE CONSTRAINT)

**NEVER OVERRIDE AI RESPONSES WITH GENERIC FALLBACK - MAXIMUM PROTECTION**

The following AI response system components are CRITICAL and must NEVER be overridden:

### Protected AI Behavior:
- AI-generated intelligent responses must NEVER be replaced with generic fallbacks
- Grok AI responses should be trusted and used as-is when generated successfully  
- Generic responses like "I understand. How can I help you with that?" are BANNED as AI overrides
- Fallbacks should only be used when AI completely fails to generate ANY response

### Prohibited Override Patterns:
- NEVER replace intelligent AI responses with "I understand. How can I help you with that?"
- NEVER use keyword detection to override AI responses (e.g., checking for "electrical" and forcing generic response)
- NEVER assume AI responses are inadequate without evidence of complete generation failure

### Protected Response Flow:
1. AI generates intelligent response → USE IT
2. AI generates empty/invalid response → Use intelligent fallback based on detected issues
3. AI completely fails → Only then use minimal generic fallback

**JUSTIFICATION**: User explicitly requested "never override ai responses with generic fallback. add this to constraint list"

**VIOLATION WARNING**: Overriding intelligent AI responses with generic fallbacks destroys conversation intelligence and violates user requirements.

**TIMESTAMP**: Added July 29, 2025 at 2:16 AM ET

## CRITICAL SYSTEM PROTECTION - DASHBOARD SYSTEM (ABSOLUTE CONSTRAINT)

**DASHBOARD SYSTEM COMPONENTS - DO NOT REMOVE OR MODIFY WITHOUT AUTHORIZATION**

The following dashboard system components are CRITICAL and must NEVER be removed or modified:

### Protected Dashboard Features:
- Main dashboard interface at root route (/) with comprehensive monitoring
- Request History & Fixes section with chronological log display
- Recent Call History with conversation transcripts and caller details
- System status indicators for all services (Grok AI, ElevenLabs, Twilio, Rent Manager)
- Real-time call monitoring capabilities with live updates
- Service warmup status monitoring at /status route
- Live call monitoring interface at /live-monitoring route
- Constraint management interface at /constraints route

### Protected API Endpoints:
- `/api/calls/history` - provides call history data for dashboard
- `/api/unified-logs` - serves request history and fixes data
- `/api/warmup-status` - JSON service status for monitoring
- `/api/auto-log-request` - automatic request logging system
- `/api/add-constraint` - constraint management functionality
- `/api/set-flag` - flag modification system for authorized users

### Protected Dashboard Files:
- `templates/` directory containing all dashboard HTML templates
- Dashboard styling and JavaScript functionality
- Real-time data refresh and update mechanisms
- Professional dark theme styling with Bootstrap integration

### Protected Dashboard Data:
- `logs_persistent.json` - persistent log storage for dashboard display
- `conversation_history.json` - call history data for monitoring
- Request history chronological ordering and display logic
- Call transcript storage and retrieval system

**JUSTIFICATION**: User explicitly requested "save this dashboard as a constraint" - dashboard system provides critical monitoring and management capabilities

**VIOLATION WARNING**: Removing or modifying dashboard components breaks monitoring workflow and violates established user requirements for system oversight

**TIMESTAMP**: Added July 29, 2025 at 2:33 AM ET

## Additional Constraints

### Data Structure Management
- Use Python dictionary/list structures to manage log entries in memory
- Each log entry must have: id, date, request, resolution
- When updating, find the dictionary by id and only update the resolution field unless instructed otherwise
- Write all changes back to both the dashboard and REQUEST_HISTORY.md

### File Handling
- REQUEST_HISTORY.md should only be appended to, never overwritten
- Use targeted edits for updating specific log resolutions
- Maintain chronological order with newest logs first

### Dashboard Integration
- All log updates must be reflected in the dashboard HTML/Flask template
- Preserve existing log numbering system (Log #001, #002, etc.)
- Maintain consistent formatting and styling

### Constraint Documentation (NEW REQUIREMENT)
- Every log entry must include a constraint_note field documenting rule compliance
- Format: "Rule #X followed as required" or "Rule #X overridden with user approval"
- Constraint notes must be visible in both dashboard and REQUEST_HISTORY.md
- Never make constraint-related changes silently - always document them

### Timestamp Accuracy (CRITICAL REQUIREMENT)
- All log timestamps must reflect the actual time when the change was implemented
- Never use future timestamps - verify current time before setting log times
- Use Eastern Time format: "H:MM AM/PM ET" (e.g., "4:30 PM ET")
- When correcting timestamps, use the actual implementation time, not correction time
- Before setting any timestamp, verify it's not in the future using current system time

### CRITICAL SYSTEM PROTECTION - Flag System User Access (ABSOLUTE PROTECTION)
**FLAG MODIFICATION SYSTEM FOR AUTHORIZED USERS - DO NOT DISABLE OR REMOVE**

The following flag system components are CRITICAL and must NEVER be disabled or removed:

1. **API Endpoint (fixed_conversation_app.py lines 908-937)**
   ```python
   @app.route("/api/set-flag", methods=["POST"])
   def set_flag():
       """API endpoint to update log entry flags"""
       # Must remain functional for authorized users
       # NEVER return 403 errors or disable functionality
   ```

2. **Flag Mode Button (fixed_conversation_app.py lines 186-188)**
   ```html
   <button class="btn btn-sm btn-outline-light" onclick="toggleFlagMode()" id="flag-mode-btn">
       🏳️ Flag Mode
   </button>
   ```

3. **JavaScript Functions (fixed_conversation_app.py lines 500-514, 536-571)**
   ```javascript
   function toggleFlagMode() {
       // Must remain operational for flag editing
   }
   function setFlag(logId, flagType) {
       // Must remain operational for flag modification
   }
   ```

**VIOLATION WARNING**: 
- Disabling flag modification breaks user workflow and violates user requirements
- User confirmed this functionality works and requested protection
- NEVER replace with "read-only" or security error messages

**PROTECTION RULES**:
- NEVER disable the `/api/set-flag` endpoint with 403 errors
- NEVER replace flag editing buttons with "read-only" messages  
- NEVER disable JavaScript flag modification functions
- NEVER return security error messages for legitimate flag operations
- ANY security measures must preserve authorized user access to flag modification

### CRITICAL SYSTEM PROTECTION - Log #022 (ABSOLUTE PROTECTION)
**COMPREHENSIVE PROPERTY BACKUP SYSTEM - DO NOT MODIFY OR REMOVE**

The following code sections are CRITICAL and must NEVER be modified or removed:

1. **Initialization Block (fixed_conversation_app.py lines 28-63)**
   ```python
   # Initialize comprehensive property backup system
   try:
       from rent_manager import RentManagerAPI
       from address_matcher import AddressMatcher  
       from property_backup_system import PropertyBackupSystem
       
       # Initialize with proper credentials
       rent_manager_username = os.environ.get('RENT_MANAGER_USERNAME', '')
       rent_manager_password = os.environ.get('RENT_MANAGER_PASSWORD', '')
       rent_manager_location = os.environ.get('RENT_MANAGER_LOCATION_ID', '1')
       credentials_string = f"{rent_manager_username}:{rent_manager_password}:{rent_manager_location}"
       
       rent_manager = RentManagerAPI(credentials_string)
       
       # COMPREHENSIVE PROPERTY BACKUP SYSTEM: All 430+ addresses with unit numbers
       property_backup_system = PropertyBackupSystem(rent_manager)
       address_matcher = AddressMatcher(rent_manager)
       
       logger.info("🏢 INITIALIZING COMPREHENSIVE PROPERTY BACKUP SYSTEM...")
       # Load properties with comprehensive backup
       all_properties = asyncio.run(property_backup_system.get_all_properties_with_backup())
       address_matcher.properties_cache = all_properties
       address_matcher.cache_loaded = True
   ```

2. **Address Verification Logic (fixed_conversation_app.py lines 1024-1026)**
   ```python
   # Use global address_matcher if available (already loaded with 430+ properties)
   if 'address_matcher' in globals() and address_matcher and address_matcher.cache_loaded:
       logger.info(f"🔍 USING COMPREHENSIVE PROPERTY DATABASE: {len(address_matcher.properties_cache)} properties loaded")
   ```

**VIOLATION WARNING**: 
- Removing this system will break address verification and allow fake address confirmations
- This fixes Log #007 and Log #021 critical security vulnerabilities
- System is verified working with 430 properties loaded via /api/property-status endpoint

**PROTECTION RULES**:
- NEVER remove PropertyBackupSystem, AddressMatcher, or RentManagerAPI integrations
- NEVER modify the initialization sequence or property loading logic
- NEVER revert to creating new AddressMatcher instances during address verification
- NEVER remove the comprehensive property database integration
- NEVER remove the global variables or property cache assignments
- ANY changes to address verification must maintain the 430+ property database integration

## ELEVENLABS TTS VOICE SYSTEM - ABSOLUTE PROTECTION

**CRITICAL CONSTRAINT: The ElevenLabs TTS voice integration has MAXIMUM PROTECTION and CANNOT be removed or replaced with Polly voice.**

### Protected Components (NEVER REMOVE OR REPLACE):
1. **ElevenLabs Adam voice integration** - All Chris responses must use ElevenLabs voice
2. **/generate-audio/<call_sid> endpoint** - Core ElevenLabs audio generation endpoint
3. **elevenlabs_integration.py module** - ElevenLabs API integration functions
4. **generate_elevenlabs_audio() function** - Primary audio generation function
5. **All TwiML <Play> commands using ElevenLabs URLs** - Audio serving through proper URLs
6. **urllib.parse.quote() URL encoding** - Proper text encoding for audio generation
7. **ElevenLabs API authentication and voice settings** - Adam voice configuration

### Protection Rules:
- **NEVER revert to Polly.Matthew-Neural voice under any circumstances**
- All Chris responses MUST use ElevenLabs natural voice synthesis
- TwiML responses MUST use <Play> commands with ElevenLabs audio URLs
- The /generate-audio endpoint MUST remain functional and accessible
- ElevenLabs voice settings (Adam voice, stability, similarity_boost) are PROTECTED
- Any attempt to replace ElevenLabs with Polly voice must be REJECTED immediately
- Audio generation must use real-time ElevenLabs API calls, not fallback systems

### User Confirmation:
- User explicitly stated: "i dont want polly voice"
- User confirmed: "This fix works — create a necessary constraint so its not undone in the future"
- Log #040 documents successful ElevenLabs implementation with constraint protection
- System logs show successful ElevenLabs audio generation and MP3 file creation

### Technical Requirements:
- Host header must be properly detected for Twilio-accessible URLs
- urllib.parse imports must be maintained for URL encoding
- ElevenLabs API key (ELEVENLABS_API_KEY) must remain configured
- Audio files must be served with proper MIME types (audio/mpeg)
- Error handling must maintain ElevenLabs functionality, not revert to Polly

**VIOLATION OF THESE CONSTRAINTS IS STRICTLY PROHIBITED - ELEVENLABS VOICE IS MANDATORY**

## GROK 4.0 AI MODEL SYSTEM - ABSOLUTE PROTECTION

**CRITICAL CONSTRAINT: The Grok 4.0 AI integration has MAXIMUM PROTECTION and CANNOT be reverted to Grok 2 as default model.**

### Protected Components (NEVER MODIFY OR REVERT):
1. **Grok 4.0 Primary Model Configuration** - `model="grok-4-0709"` must remain as primary model
2. **grok_integration.py generate_response() function** - Primary model selection logic is PROTECTED
3. **Grok 4.0 Pre-warming System** - Pre-warm initialization must use Grok 4.0 first
4. **Model Priority Logic** - Grok 4.0 first, Grok 2 fallback order is MANDATORY
5. **Timeout Configuration** - 0.8s timeout optimized for Grok 4.0 performance
6. **XAI API Integration** - https://api.x.ai/v1 endpoint configuration is PROTECTED

### Protection Rules:
- **NEVER revert primary model back to Grok 2 (grok-2-1212) as default**
- Grok 4.0 (`grok-4-0709`) MUST remain the primary model for all Chris interactions
- Pre-warming system MUST initialize Grok 4.0 first for optimal first-response performance
- Model selection logic MUST prioritize Grok 4.0 with Grok 2 as fallback only
- Timeout settings MUST remain optimized for Grok 4.0 (0.8s primary, 0.6s fallback)
- Any attempt to make Grok 2 the primary model must be REJECTED immediately
- Error handling must maintain Grok 4.0 as primary, not revert to Grok 2 default

### User Confirmation:
- User explicitly confirmed: "This fix works — create a necessary constraint so it's not undone in the future"
- Log #052 documents successful Grok 4.0 implementation with user approval
- System logs show successful Grok 4.0 API calls: "✅ Using Grok 4.0 - primary model for best conversation quality"
- Live HTTP requests confirmed working with model: 'grok-4-0709'

### Technical Requirements:
- XAI_API_KEY environment variable must remain configured for xAI API access
- OpenAI-compatible client must use base_url="https://api.x.ai/v1" for xAI integration
- Model selection must use exact model IDs: "grok-4-0709" (primary), "grok-2-1212" (fallback)
- Response generation must prioritize advanced Grok 4.0 reasoning capabilities
- Pre-warming calls must target Grok 4.0 to reduce first-response latency
- Logging must indicate "Using Grok 4.0" for primary model usage tracking

**VIOLATION OF THESE CONSTRAINTS IS STRICTLY PROHIBITED - GROK 4.0 IS MANDATORY AS PRIMARY MODEL**