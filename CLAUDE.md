# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Windows System Monitoring toolkit that tracks system-level events, administrative actions, and configuration changes on Windows systems. The project includes both Python (using pywin32) and PowerShell implementations.

**Platform Requirement**: Windows only (Linux/macOS cannot execute these scripts properly)

## Key Commands

### Installation
```bash
pip install -r requirements.txt
```

If pywin32 fails to install:
```bash
pip install --upgrade pywin32
python -m pywin32_postinstall
```

### Running the Monitors

**Windows System Monitor** (comprehensive monitoring):
```bash
python windows_monitor.py
```

**Administrative Actions Monitor** (admin-focused):
```bash
python admin_actions_monitor.py
```

**PowerShell Equivalent**:
```powershell
powershell -ExecutionPolicy Bypass -File Admin-Monitor-PowerShell.ps1
```

### Testing

**Dependency verification**:
```bash
python test_dependencies.py
```

**Admin monitor test**:
```bash
python test_admin_monitor.py
```

**Interactive demo**:
```bash
python example_usage.py
```

## Architecture

### Core Components

The system consists of two main monitoring frameworks:

#### 1. WindowsMonitor (`windows_monitor.py`)
Main orchestrator class that manages multiple specialized monitors through threaded architecture:

- **ProcessMonitor**: Tracks process creation/termination using psutil
- **RegistryMonitor**: Snapshot-based registry change detection using winreg
- **FileSystemMonitor**: Watchdog-based file system event monitoring
- **EventLogMonitor**: Windows Event Log polling via win32evtlog
- **NetworkAdapterMonitor**: Network adapter change detection
- **DeviceMonitor**: Device connection/disconnection tracking (TODO)
- **ServiceMonitor**: Windows service state monitoring

**Threading Model**: Each monitor runs in its own daemon thread, polling at configurable intervals (default: 5 seconds).

**Event Storage**: Events are collected in-memory (up to max_events limit) and persisted to JSON file on each event.

#### 2. AdminActionsMonitor (`admin_actions_monitor.py`)
Focused on administrative actions with PowerShell command equivalents:

- **Service Changes**: Tracks service state transitions via win32service API
- **User Account Changes**: Monitors user flags and account status via win32net
- **Policy Changes**: Detects security policy modifications using WMI
- **Registry Changes**: Monitors critical auto-start and service keys
- **Security Changes**: Checks privilege escalation and token information
- **System Configuration**: Tracks domain, workgroup, and hardware changes

**Key Feature**: Each logged action includes equivalent PowerShell command for manual verification.

### Configuration

Both monitors use JSON configuration files:

**windows_monitor.py** → `monitor_config.json`
- Enable/disable monitoring components
- Paths to watch for file system changes
- Registry keys to monitor
- Event logs to poll
- Output file, log level, max events, check interval

**admin_actions_monitor.py** → Uses default configuration (30-second polling)
- No external config file
- Hard-coded critical registry keys
- Critical services list

### Data Flow

```
Windows System Events
    ↓
Monitor Classes (threading.Thread)
    ↓
WindowsMonitor.log_event() / AdminActionsMonitor._log_action()
    ↓
In-memory events list + JSON file output + Logging
```

### Output Files

- `monitor_events.json` - WindowsMonitor event storage
- `windows_monitor.log` - WindowsMonitor log file
- `admin_actions.json` - AdminActionsMonitor event storage (append-only)
- `admin_actions.log` - AdminActionsMonitor log file
- `admin_actions_report_*.json` - Exported reports with summaries

## Development Notes

### Windows API Usage

The codebase uses pywin32 extensively. Key APIs:

- **win32evtlog**: Event log reading (requires admin for Security log)
- **win32service**: Service enumeration and status
- **win32net**: User account information
- **win32security**: Token information and privileges
- **winreg**: Registry access (HKEY_LOCAL_MACHINE requires elevation for some keys)
- **wmi**: System information queries

### Privilege Requirements

- **Basic functionality**: Standard user privileges
- **Security Event Log**: Administrator privileges required
- **Some registry keys**: Administrator privileges required
- **Service management**: Read-only access works without elevation

Test admin status using `test_dependencies.py` which checks via `win32security.TokenElevation`.

### Event Structure

All events follow this schema:
```json
{
  "timestamp": "ISO 8601 format",
  "type": "EVENT_TYPE",
  "data": {
    // Event-specific fields
  }
}
```

AdminAction dataclass adds:
- user
- process
- description
- powershell_command
- severity (INFO/WARNING/HIGH)

### Code Organization

- **Monitor classes**: Each contains `__init__(main_monitor)` and `monitor()` method
- **Daemon threads**: All monitoring threads are daemon=True (exit with main thread)
- **Error handling**: Try-except blocks with logging, continue monitoring on errors
- **Polling intervals**: Configurable via `check_interval` (5-30 seconds typical)

### Testing Considerations

This codebase is designed for **Windows execution only**. When developing:

1. **Cannot run on Linux/macOS**: pywin32 libraries will fail to import
2. **Mock testing approach**: Test files verify imports and demonstrate usage
3. **Dependency testing**: `test_dependencies.py` verifies environment before monitoring
4. **Admin testing**: Some features require "Run as Administrator"

### Adding New Monitors

To add a new monitor to WindowsMonitor:

1. Create monitor class with `__init__(self, main_monitor)` and `monitor(self)` method
2. Add instance in `WindowsMonitor.__init__()`
3. Add configuration flag in default_config['monitoring']
4. Add thread start in `start_monitoring()` method
5. Use `self.main_monitor.log_event(type, data)` to record events
6. Include `while self.main_monitor.running:` loop with sleep intervals

### PowerShell Equivalents

The `Admin-Monitor-PowerShell.ps1` script demonstrates PowerShell cmdlets equivalent to Python pywin32 calls:

- `Get-Service` → win32service.EnumServicesStatus
- `Get-LocalUser` → win32net.NetUserEnum
- `Get-ItemProperty` → winreg.OpenKey/EnumValue
- `Get-WinEvent` → win32evtlog.ReadEventLog
- `whoami /priv` → win32security.GetTokenInformation

When extending functionality, consider documenting PowerShell equivalents for manual verification.

## Important Files

- **windows_monitor.py** (652 lines): Main system monitor with 7 monitoring components
- **admin_actions_monitor.py** (483 lines): Administrative actions monitor with PowerShell equivalents
- **requirements.txt**: Dependencies (psutil, pywin32, watchdog, WMI)
- **test_dependencies.py**: Pre-flight dependency and permission checking
- **example_usage.py**: Interactive demo with menu system
- **Admin-Monitor-PowerShell.ps1**: PowerShell implementation reference
