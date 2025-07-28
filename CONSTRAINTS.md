# Logging Rules

1. Never overwrite or delete logs from the Request History dashboard.
2. Only append new entries or update the resolution of a specific log (e.g., log #007).
3. Never modify or remove the original request text unless explicitly instructed.
4. Always mirror each log update to the file REQUEST_HISTORY.md.
5. Logs should be ordered from newest to oldest in the dashboard view.

Before updating the UI or any logs, read this file and confirm you're following the rules.

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