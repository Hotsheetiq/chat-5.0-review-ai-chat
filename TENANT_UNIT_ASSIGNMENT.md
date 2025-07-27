# Tenant-Specific Unit Assignment System

## How Chris Ensures Correct Unit Assignment

When a tenant calls about issues in multi-unit buildings (like "25 Port Richmond Avenue" with apartments + store), Chris uses a sophisticated system to ensure complaints are attached to the correct unit:

### 1. **Caller Phone Lookup**
- Chris automatically looks up the caller's phone number in the Rent Manager tenant database
- Uses `rent_manager.lookup_tenant_by_phone(caller_phone)` to identify the specific tenant
- Gets tenant name, registered address, and unit information

### 2. **Address Cross-Verification**
- Compares the address the caller mentions with their registered address in the system
- Ensures the caller is authorized to report issues for that specific unit
- Logs any address mismatches for security

### 3. **Unit-Specific Ticket Creation**
Service tickets include complete tenant information:
```python
current_service_issue = {
    'issue_type': 'electrical',
    'address': '25 Port Richmond Avenue, Apt 2',  # Specific unit
    'tenant_name': 'John Smith',
    'tenant_phone': '+15551234567',
    'specific_unit': 'Apt 2',
    'issue_number': 'SV-12345'
}
```

### 4. **Multi-Unit Building Detection**
- Identifies buildings with multiple units (158-A, 158-B, 158-C, 158-D Port Richmond Avenue)
- If caller gives base address ("158 Port Richmond"), asks for unit clarification
- "I found multiple units at that address: 158-A, 158-B, 158-C, 158-D Port Richmond Avenue. Could you please specify which unit you're calling about?"

### 5. **Enhanced Response Confirmation**
Chris confirms the specific unit in responses:
- "Perfect! I've created service ticket #SV-12345 for your electrical issue at 25 Port Richmond Avenue (Unit: Apt 2)."

## Example Scenarios

### Scenario 1: Known Tenant Calling
- **Caller**: Tenant at 25 Port Richmond Ave, Apt 2
- **Phone**: +15551234567 (registered in system)
- **Process**: Phone lookup → Tenant identified → Unit confirmed → Ticket assigned to specific unit

### Scenario 2: Unknown Caller
- **Caller**: Not in tenant database
- **Process**: Address verification → General inquiry handling → Unit clarification required

### Scenario 3: Multi-Unit Building
- **Caller**: "158 Port Richmond Avenue"
- **System**: Detects 4 units (A, B, C, D)
- **Response**: "Which unit are you calling about: 158-A, 158-B, 158-C, or 158-D?"

## Technical Implementation

The system uses:
- **Rent Manager API**: `lookup_tenant_by_phone()` for tenant identification
- **Address Verification**: Cross-references caller phone with registered address
- **Unit Detection**: Identifies multi-unit properties using naming patterns (-A, -B, etc.)
- **Secure Assignment**: Only creates tickets for verified tenant-address combinations

This ensures maintenance teams receive accurate information about which specific unit needs service, preventing confusion in multi-tenant buildings.