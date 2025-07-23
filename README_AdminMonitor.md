# Administrative Actions Monitoring

This implementation provides comprehensive monitoring of administrative actions and system configuration changes on Windows systems using `pywin32` and equivalent PowerShell commands.

## Features

### 🔍 Monitoring Capabilities

1. **Service Changes**
   - Monitor Windows service state changes (start, stop, pause)
   - Track critical system services
   - Log service events from Windows Event Log
   - PowerShell equivalent: `Get-Service`, `Get-WinEvent`

2. **User Account Changes** 
   - Monitor local user account modifications
   - Track account flags (enabled/disabled, password settings)
   - Detect suspicious account configurations
   - PowerShell equivalent: `Get-LocalUser`, Security Event Log

3. **Security Policy Changes**
   - Monitor account policies and security settings
   - Track UAC (User Account Control) configuration
   - Detect policy modifications
   - PowerShell equivalent: `secedit`, Registry queries

4. **Registry Monitoring**
   - Monitor critical registry keys (Run keys, Services, Winlogon)
   - Detect suspicious registry entries
   - Track startup program changes
   - PowerShell equivalent: `Get-ItemProperty`, `Get-ChildItem`

5. **System Configuration**
   - Monitor system information changes
   - Track network adapter configuration
   - Monitor Windows Firewall status
   - PowerShell equivalent: `Get-ComputerInfo`, `Get-NetAdapter`

6. **Security Events**
   - Monitor user privileges and escalation attempts
   - Track security-related events
   - Log administrative access
   - PowerShell equivalent: `whoami /priv`, Security Event Log

## Files

### Python Implementation
- `admin_actions_monitor.py` - Main monitoring system using pywin32
- `test_admin_monitor.py` - Test script with demonstrations
- `requirements.txt` - Python dependencies

### PowerShell Implementation  
- `Admin-Monitor-PowerShell.ps1` - Equivalent PowerShell monitoring script

### Output Files
- `admin_actions.log` - Text-based activity log
- `admin_actions.json` - JSON-formatted log entries
- `admin_actions_report_*.json` - Detailed reports with summaries

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure you have administrative privileges for full monitoring capabilities.

## Usage

### Python Monitoring

#### Basic Usage
```python
python admin_actions_monitor.py
```

#### Programmatic Usage
```python
from admin_actions_monitor import AdminActionsMonitor

monitor = AdminActionsMonitor()
monitor.start_monitoring()

# Monitor runs in background thread
# Press Ctrl+C to stop and export report
```

### PowerShell Monitoring

```powershell
# Run the PowerShell monitoring script
powershell -ExecutionPolicy Bypass -File Admin-Monitor-PowerShell.ps1
```

### Testing
```python
python test_admin_monitor.py
```

## Key PowerShell Commands

### Service Monitoring
```powershell
# List all services with status
Get-Service | Select-Object Name,Status,StartType,ServiceType

# Check specific critical service
Get-Service -Name "Spooler" | Format-List *

# Monitor service events
Get-WinEvent -FilterHashtable @{LogName='System'; ID=7034,7035,7036; StartTime=(Get-Date).AddHours(-1)}
```

### User Account Monitoring
```powershell
# List local users
Get-LocalUser | Select-Object Name,Enabled,PasswordRequired,UserMayChangePassword

# Check for accounts without password requirements
Get-LocalUser | Where-Object {$_.Enabled -and -not $_.PasswordRequired}

# Monitor logon events (requires elevation)
Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624; StartTime=(Get-Date).AddHours(-1)}
```

### Registry Monitoring
```powershell
# Monitor startup programs
Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
Get-ItemProperty "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"

# Check system services in registry
Get-ChildItem "HKLM:\\SYSTEM\\CurrentControlSet\\Services" | Select-Object Name
```

### Security Policy Monitoring
```powershell
# Export and check security policies
secedit /export /cfg temp_policy.cfg
Get-Content temp_policy.cfg | Where-Object {$_ -match "Password"}

# Check UAC settings
Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System" | Select-Object EnableLUA,ConsentPromptBehaviorAdmin

# Check current user privileges
whoami /priv
```

### System Configuration
```powershell
# Get system information
Get-ComputerInfo | Select-Object WindowsProductName,TotalPhysicalMemory,Domain,Workgroup

# Check network adapters
Get-NetAdapter | Where-Object {$_.Status -eq "Up"} | Select-Object Name,InterfaceDescription,LinkSpeed

# Monitor firewall status
Get-NetFirewallProfile | Select-Object Name,Enabled
```

## Security Considerations

### Elevated Privileges
- Many monitoring functions require administrative privileges
- Security Event Log access requires elevation
- Some registry keys require elevated access
- UAC may prompt for permission

### Event Log Access
- Security Event Log requires administrative privileges
- System Event Log is generally accessible to standard users
- Application Event Log access varies by configuration

### Registry Access
- HKEY_LOCAL_MACHINE requires elevated access for some keys
- HKEY_CURRENT_USER is accessible to the current user
- Some system registry keys are protected

## Monitoring Output

### Log Formats

#### Text Log (admin_actions.log)
```
2024-01-15T10:30:45 - SERVICE_STATE_CHANGE - Service 'Spooler' state changed from STOPPED to RUNNING
2024-01-15T10:30:46 - USER_ACCOUNT_CHECK - User account status: Administrator - Enabled: True
```

#### JSON Log (admin_actions.json)
```json
{
  "timestamp": "2024-01-15T10:30:45",
  "action_type": "SERVICE_STATE_CHANGE", 
  "description": "Service 'Spooler' state changed from STOPPED to RUNNING",
  "user": "Klaus",
  "process": "system",
  "details": {
    "service_name": "Spooler",
    "old_state": "STOPPED",
    "new_state": "RUNNING"
  },
  "powershell_command": "Get-Service -Name 'Spooler' | Select-Object Name,Status,StartType,ServiceType",
  "severity": "WARNING"
}
```

### Report Structure
The exported reports include:
- Total action count
- Actions by category (services, users, policies, registry)
- High-severity events summary
- Detailed action history

## Integration

### With SIEM Systems
The JSON output format is compatible with most SIEM systems for log ingestion and analysis.

### With PowerShell Scripts
The PowerShell equivalent commands can be integrated into existing administrative scripts.

### With Task Scheduler
Both Python and PowerShell versions can be scheduled to run periodically using Windows Task Scheduler.

## Troubleshooting

### Common Issues

1. **Access Denied Errors**
   - Run as Administrator for full functionality
   - Some features require elevated privileges

2. **WMI Connection Issues**
   - Ensure WMI service is running
   - Check Windows firewall settings
   - Verify user has WMI permissions

3. **Event Log Access**
   - Security Event Log requires administrative privileges
   - Enable audit policies if events are missing

4. **Registry Access**
   - Some registry keys require elevation
   - UAC may block access to protected keys

### Performance Considerations
- Monitoring runs every 30 seconds by default
- Large numbers of services/users may impact performance
- Event log queries are limited to recent events
- Registry monitoring focuses on critical keys only

## Architecture

### Python Implementation
- Uses `pywin32` for direct Windows API access
- WMI for system information queries
- Threading for background monitoring
- JSON logging for structured data

### PowerShell Implementation
- Native PowerShell cmdlets
- Windows Event Log integration
- Registry PowerShell provider
- Structured logging functions

Both implementations provide equivalent functionality with similar output formats for consistency.
