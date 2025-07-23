# Windows System Monitor

A comprehensive Python script for monitoring Windows system-level events, administrative actions, and registry changes in real-time.

## Features

- **Process Monitoring**: Track process creation, termination, and changes
- **Registry Monitoring**: Monitor Windows registry changes in key locations
- **File System Monitoring**: Watch for file/directory creation, deletion, modification, and moves
- **Event Log Monitoring**: Monitor Windows Event Logs (System, Security, Application)
- **Network Monitoring**: Track new network connections
- **Configurable**: Fully configurable monitoring parameters
- **Event Storage**: Store events in JSON format with optional rotation
- **Logging**: Comprehensive logging with configurable levels

## Requirements

- Windows Operating System
- Python 3.7+
- Administrator privileges (recommended for full functionality)

## Installation

1. Clone or download the script files
2. Install required dependencies:

```bash
pip install -r requirements.txt
```

### Dependencies

- **psutil**: System and process utilities
- **pywin32**: Windows API access
- **watchdog**: File system event monitoring

## Usage

### Basic Usage

Run the monitor with default settings:

```bash
python windows_monitor.py
```

### Configuration

The script creates a `monitor_config.json` file on first run with default settings. You can modify this file to customize monitoring behavior:

```json
{
  "monitoring": {
    "processes": true,
    "registry": true,
    "filesystem": true,
    "event_logs": true,
    "network": true
  },
  "paths_to_watch": [
    "C:\\Windows\\System32",
    "C:\\Program Files",
    "C:\\Users"
  ],
  "registry_keys": [
    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
    "HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
    "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services"
  ],
  "event_logs": [
    "System",
    "Security",
    "Application"
  ],
  "output_file": "monitor_events.json",
  "log_level": "INFO",
  "max_events": 1000,
  "check_interval": 5
}
```

### Configuration Options

- **monitoring**: Enable/disable specific monitoring components
- **paths_to_watch**: File system paths to monitor for changes
- **registry_keys**: Registry keys to monitor for changes
- **event_logs**: Windows Event Logs to monitor
- **output_file**: JSON file to store captured events
- **log_level**: Logging level (DEBUG, INFO, WARNING, ERROR)
- **max_events**: Maximum number of events to keep in memory
- **check_interval**: Seconds between monitoring checks

## Output Files

### Event Storage
- `monitor_events.json`: JSON file containing all captured events
- `windows_monitor.log`: Log file with detailed monitoring information

### Event Types

The monitor captures the following event types:

1. **PROCESS_CREATED**: New process started
2. **PROCESS_TERMINATED**: Process ended
3. **REGISTRY_VALUE_ADDED**: New registry value created
4. **REGISTRY_VALUE_MODIFIED**: Registry value changed
5. **REGISTRY_VALUE_DELETED**: Registry value removed
6. **FILE_CREATED**: File or directory created
7. **FILE_DELETED**: File or directory deleted
8. **FILE_MODIFIED**: File modified
9. **FILE_MOVED**: File or directory moved/renamed
10. **NEW_NETWORK_CONNECTION**: New network connection established
11. **WINDOWS_EVENT_LOG**: Windows Event Log entry

### Event Structure

Each event follows this structure:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "type": "EVENT_TYPE",
  "data": {
    // Event-specific data
  }
}
```

## Security Considerations

- **Administrator Privileges**: Required for monitoring system-level events and accessing Security event logs
- **Performance Impact**: File system monitoring of large directories may impact performance
- **Privacy**: The monitor captures detailed system activity - ensure compliance with local policies
- **Storage**: Event files can grow large over time - consider implementing rotation

## Advanced Usage

### Custom Registry Keys

Add additional registry keys to monitor by modifying the `registry_keys` array in the configuration:

```json
"registry_keys": [
  "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
  "HKEY_CURRENT_USER\\SOFTWARE\\Custom\\Application",
  "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Session Manager"
]
```

### Selective Monitoring

Disable specific monitoring components by setting them to `false` in the configuration:

```json
"monitoring": {
  "processes": true,
  "registry": false,
  "filesystem": true,
  "event_logs": true,
  "network": false
}
```

### Custom File Paths

Monitor specific directories by modifying the `paths_to_watch` array:

```json
"paths_to_watch": [
  "C:\\Windows\\System32",
  "C:\\Program Files",
  "C:\\Users\\%USERNAME%\\Documents",
  "D:\\ImportantData"
]
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Run as Administrator for full functionality
2. **Missing Dependencies**: Install all required packages via pip
3. **High CPU Usage**: Reduce monitoring frequency by increasing `check_interval`
4. **Large Event Files**: Reduce `max_events` or implement custom rotation

### Error Handling

The script includes comprehensive error handling and will continue monitoring even if individual components fail. Check the log file for detailed error information.

## Performance Tuning

- **Check Interval**: Increase for lower CPU usage, decrease for more responsive monitoring
- **Path Filtering**: Monitor only necessary directories to reduce file system overhead
- **Event Limits**: Adjust `max_events` based on available memory and storage
- **Log Level**: Use INFO or WARNING in production to reduce log overhead

## License

This script is provided as-is for educational and monitoring purposes. Ensure compliance with your organization's security and privacy policies before deployment.

## Contributing

Feel free to submit issues, feature requests, or improvements to enhance the monitoring capabilities.
