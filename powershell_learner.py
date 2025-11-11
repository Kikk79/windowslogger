#!/usr/bin/env python3
"""
PowerShell Learner - Main Application
Monitors Windows system actions and displays equivalent PowerShell commands in real-time.

This tool helps users learn PowerShell by showing the command equivalents of their GUI actions.
"""

import sys
import time
import threading
from typing import Dict, Any, Optional

# Import our monitoring components
from windows_monitor import WindowsMonitor
from admin_actions_monitor import AdminActionsMonitor
from powershell_learner_gui import PowerShellLearnerGUI


class PowerShellCommandGenerator:
    """Generates PowerShell command equivalents for Windows actions"""

    @staticmethod
    def generate_command(event_type: str, data: Dict[str, Any]) -> str:
        """
        Generate a PowerShell command based on the event type and data

        Args:
            event_type: Type of event (e.g., "SERVICE_STATUS_CHANGED")
            data: Event data dictionary

        Returns:
            PowerShell command string
        """

        # Service-related commands
        if event_type == "SERVICE_STATUS_CHANGED":
            service_name = data.get('name', 'ServiceName')
            new_status = data.get('new_status', 'UNKNOWN')

            if new_status == "RUNNING":
                return f"Start-Service -Name '{service_name}'"
            elif new_status == "STOPPED":
                return f"Stop-Service -Name '{service_name}'"
            elif new_status == "PAUSED":
                return f"Suspend-Service -Name '{service_name}'"
            else:
                return f"Get-Service -Name '{service_name}' | Format-List *"

        # Registry-related commands
        elif event_type == "REGISTRY_VALUE_ADDED":
            key_path = data.get('key_path', 'HKLM:\\SOFTWARE\\...')
            value_name = data.get('value_name', 'ValueName')
            value_data = data.get('value_data', 'ValueData')
            return f"Set-ItemProperty -Path '{key_path}:' -Name '{value_name}' -Value '{value_data}'"

        elif event_type == "REGISTRY_VALUE_MODIFIED":
            key_path = data.get('key_path', 'HKLM:\\SOFTWARE\\...')
            value_name = data.get('value_name', 'ValueName')
            new_value = data.get('new_value', 'NewValue')
            return f"Set-ItemProperty -Path '{key_path}:' -Name '{value_name}' -Value '{new_value}'"

        elif event_type == "REGISTRY_VALUE_DELETED":
            key_path = data.get('key_path', 'HKLM:\\SOFTWARE\\...')
            value_name = data.get('value_name', 'ValueName')
            return f"Remove-ItemProperty -Path '{key_path}:' -Name '{value_name}'"

        # Process-related commands
        elif event_type == "PROCESS_CREATED":
            process_name = data.get('name', 'process.exe')
            exe_path = data.get('exe', '')

            if exe_path:
                return f"Start-Process -FilePath '{exe_path}'"
            else:
                return f"Start-Process -FilePath '{process_name}'"

        elif event_type == "PROCESS_TERMINATED":
            process_name = data.get('name', 'process.exe')
            pid = data.get('pid', 0)
            return f"Stop-Process -Name '{process_name}' # or Stop-Process -Id {pid}"

        # File system commands
        elif event_type == "FILE_CREATED":
            path = data.get('path', 'C:\\path\\to\\file')
            is_directory = data.get('is_directory', False)

            if is_directory:
                return f"New-Item -Path '{path}' -ItemType Directory"
            else:
                return f"New-Item -Path '{path}' -ItemType File"

        elif event_type == "FILE_DELETED":
            path = data.get('path', 'C:\\path\\to\\file')
            return f"Remove-Item -Path '{path}'"

        elif event_type == "FILE_MODIFIED":
            path = data.get('path', 'C:\\path\\to\\file')
            return f"# File modified: {path}\nGet-Item '{path}' | Select-Object LastWriteTime"

        elif event_type == "FILE_MOVED":
            src_path = data.get('src_path', 'C:\\source\\file')
            dest_path = data.get('dest_path', 'C:\\destination\\file')
            return f"Move-Item -Path '{src_path}' -Destination '{dest_path}'"

        # Network commands
        elif event_type == "NEW_NETWORK_CONNECTION":
            local_addr = data.get('local_address', '0.0.0.0:0')
            remote_addr = data.get('remote_address', '0.0.0.0:0')
            process_name = data.get('process_name', 'process.exe')
            return f"Get-NetTCPConnection | Where-Object {{$_.LocalAddress -eq '{local_addr}' -and $_.OwningProcess -eq (Get-Process -Name '{process_name}').Id}}"

        elif event_type == "NETWORK_ADAPTER_ADDED":
            name = data.get('name', 'AdapterName')
            return f"Get-NetAdapter -Name '{name}' | Format-List *"

        elif event_type == "NETWORK_ADAPTER_REMOVED":
            name = data.get('name', 'AdapterName')
            return f"# Adapter removed: {name}\nGet-NetAdapter | Where-Object {{$_.Name -ne '{name}'}}"

        # User account commands
        elif event_type == "USER_ACCOUNT_CHANGE":
            username = data.get('username', 'Username')
            changes = data.get('changes', [])

            if any('disabled' in str(c).lower() for c in changes):
                if any('Account Disabled enabled' in str(c) for c in changes):
                    return f"Disable-LocalUser -Name '{username}'"
                else:
                    return f"Enable-LocalUser -Name '{username}'"

            return f"Get-LocalUser -Name '{username}' | Format-List *"

        # Event log commands
        elif event_type == "WINDOWS_EVENT_LOG":
            log_name = data.get('log_name', 'System')
            event_id = data.get('event_id', 0)
            return f"Get-WinEvent -FilterHashtable @{{LogName='{log_name}'; ID={event_id}; StartTime=(Get-Date).AddHours(-1)}} -MaxEvents 10"

        # Firewall commands
        elif event_type == "FIREWALL_RULE_ADDED":
            rule_name = data.get('rule_name', 'RuleName')
            return f"Get-NetFirewallRule -Name '{rule_name}' | Format-List *"

        elif event_type == "FIREWALL_RULE_REMOVED":
            rule_name = data.get('rule_name', 'RuleName')
            return f"Remove-NetFirewallRule -Name '{rule_name}'"

        # Scheduled Task commands
        elif event_type == "SCHEDULED_TASK_CREATED":
            task_name = data.get('task_name', 'TaskName')
            return f"Get-ScheduledTask -TaskName '{task_name}' | Format-List *"

        elif event_type == "SCHEDULED_TASK_DELETED":
            task_name = data.get('task_name', 'TaskName')
            return f"Unregister-ScheduledTask -TaskName '{task_name}' -Confirm:$false"

        elif event_type == "SCHEDULED_TASK_STATE_CHANGED":
            task_name = data.get('task_name', 'TaskName')
            new_state = data.get('new_state', 'Unknown')

            if new_state == "Disabled":
                return f"Disable-ScheduledTask -TaskName '{task_name}'"
            elif new_state == "Ready":
                return f"Enable-ScheduledTask -TaskName '{task_name}'"
            else:
                return f"Get-ScheduledTask -TaskName '{task_name}'"

        # Environment Variable commands
        elif event_type == "ENV_VAR_ADDED":
            var_name = data.get('variable_name', 'VARIABLE_NAME')
            value = data.get('value', 'value')
            return f"[Environment]::SetEnvironmentVariable('{var_name}', '{value}', 'Machine')"

        elif event_type == "ENV_VAR_MODIFIED":
            var_name = data.get('variable_name', 'VARIABLE_NAME')
            new_value = data.get('new_value', 'new_value')
            return f"[Environment]::SetEnvironmentVariable('{var_name}', '{new_value}', 'Machine')"

        elif event_type == "ENV_VAR_DELETED":
            var_name = data.get('variable_name', 'VARIABLE_NAME')
            return f"[Environment]::SetEnvironmentVariable('{var_name}', $null, 'Machine')"

        # Windows Feature commands
        elif event_type == "WINDOWS_FEATURE_CHANGED":
            feature_name = data.get('feature_name', 'FeatureName')
            new_state = data.get('new_state', 'Unknown')

            if 'Enabled' in str(new_state):
                return f"Enable-WindowsOptionalFeature -Online -FeatureName '{feature_name}' -NoRestart"
            else:
                return f"Disable-WindowsOptionalFeature -Online -FeatureName '{feature_name}' -NoRestart"

        elif event_type == "WINDOWS_FEATURE_DETECTED":
            feature_name = data.get('feature_name', 'FeatureName')
            return f"Get-WindowsOptionalFeature -Online -FeatureName '{feature_name}'"

        # Printer commands
        elif event_type == "PRINTER_ADDED":
            printer_name = data.get('printer_name', 'PrinterName')
            driver = data.get('driver', 'DriverName')
            return f"Add-Printer -Name '{printer_name}' -DriverName '{driver}' -PortName 'LPT1:'"

        elif event_type == "PRINTER_REMOVED":
            printer_name = data.get('printer_name', 'PrinterName')
            return f"Remove-Printer -Name '{printer_name}'"

        # Default
        else:
            return f"# PowerShell command for {event_type} not yet implemented"

    @staticmethod
    def get_description(event_type: str, data: Dict[str, Any]) -> str:
        """
        Generate a human-readable description of the event

        Args:
            event_type: Type of event
            data: Event data dictionary

        Returns:
            Description string
        """

        if event_type == "SERVICE_STATUS_CHANGED":
            name = data.get('name', 'Unknown')
            old_status = data.get('old_status', 'UNKNOWN')
            new_status = data.get('new_status', 'UNKNOWN')
            return f"Service '{name}' changed from {old_status} to {new_status}"

        elif event_type == "REGISTRY_VALUE_ADDED":
            key_path = data.get('key_path', 'Unknown')
            value_name = data.get('value_name', 'Unknown')
            return f"Registry value '{value_name}' added to {key_path}"

        elif event_type == "REGISTRY_VALUE_MODIFIED":
            key_path = data.get('key_path', 'Unknown')
            value_name = data.get('value_name', 'Unknown')
            return f"Registry value '{value_name}' modified in {key_path}"

        elif event_type == "REGISTRY_VALUE_DELETED":
            key_path = data.get('key_path', 'Unknown')
            value_name = data.get('value_name', 'Unknown')
            return f"Registry value '{value_name}' deleted from {key_path}"

        elif event_type == "PROCESS_CREATED":
            name = data.get('name', 'Unknown')
            pid = data.get('pid', 0)
            return f"Process '{name}' started (PID: {pid})"

        elif event_type == "PROCESS_TERMINATED":
            name = data.get('name', 'Unknown')
            pid = data.get('pid', 0)
            return f"Process '{name}' terminated (PID: {pid})"

        elif event_type == "FILE_CREATED":
            path = data.get('path', 'Unknown')
            is_directory = data.get('is_directory', False)
            item_type = "Directory" if is_directory else "File"
            return f"{item_type} created: {path}"

        elif event_type == "FILE_DELETED":
            path = data.get('path', 'Unknown')
            is_directory = data.get('is_directory', False)
            item_type = "Directory" if is_directory else "File"
            return f"{item_type} deleted: {path}"

        elif event_type == "FILE_MODIFIED":
            path = data.get('path', 'Unknown')
            return f"File modified: {path}"

        elif event_type == "FILE_MOVED":
            src_path = data.get('src_path', 'Unknown')
            dest_path = data.get('dest_path', 'Unknown')
            return f"Item moved from {src_path} to {dest_path}"

        elif event_type == "NEW_NETWORK_CONNECTION":
            remote_addr = data.get('remote_address', 'Unknown')
            process_name = data.get('process_name', 'Unknown')
            return f"New network connection to {remote_addr} by {process_name}"

        elif event_type == "NETWORK_ADAPTER_ADDED":
            name = data.get('name', 'Unknown')
            return f"Network adapter added: {name}"

        elif event_type == "NETWORK_ADAPTER_REMOVED":
            name = data.get('name', 'Unknown')
            return f"Network adapter removed: {name}"

        elif event_type == "USER_ACCOUNT_CHANGE":
            username = data.get('username', 'Unknown')
            changes = data.get('changes', [])
            change_str = ', '.join(str(c) for c in changes) if changes else 'Account modified'
            return f"User account '{username}': {change_str}"

        elif event_type == "WINDOWS_EVENT_LOG":
            log_name = data.get('log_name', 'Unknown')
            event_id = data.get('event_id', 0)
            return f"Event Log entry in {log_name} (ID: {event_id})"

        else:
            return f"{event_type}: {str(data)[:100]}"


class PowerShellLearner:
    """
    Main application class that integrates monitoring with PowerShell command generation
    """

    def __init__(self):
        self.gui = PowerShellLearnerGUI(title="PowerShell Learner - Live Command Feed")
        self.windows_monitor = None
        self.admin_monitor = None
        self.cmd_generator = PowerShellCommandGenerator()
        self.running = False

    def start(self):
        """Start the PowerShell Learner application"""
        print("Starting PowerShell Learner...")
        print("=" * 60)

        # Start GUI
        print("Initializing GUI...")
        self.gui.start()
        time.sleep(1)  # Wait for GUI to initialize

        # Start Windows Monitor
        print("Starting Windows system monitor...")
        self.windows_monitor = WindowsMonitor()

        # Hook into the log_event method to intercept events
        original_log_event = self.windows_monitor.log_event

        def hooked_log_event(event_type: str, event_data: Dict[str, Any]):
            # Call original method
            original_log_event(event_type, event_data)

            # Send to GUI with PowerShell command
            ps_command = self.cmd_generator.generate_command(event_type, event_data)
            description = self.cmd_generator.get_description(event_type, event_data)

            self.gui.add_event(
                event_type=event_type,
                description=description,
                powershell_command=ps_command,
                details=event_data
            )

        # Replace the method
        self.windows_monitor.log_event = hooked_log_event

        # Start monitoring
        self.windows_monitor.start_monitoring()

        self.running = True
        print("✓ PowerShell Learner is running!")
        print("  Watch the GUI for real-time PowerShell commands")
        print("  Press Ctrl+C to stop...")
        print("=" * 60)

    def stop(self):
        """Stop the application"""
        print("\nStopping PowerShell Learner...")
        self.running = False

        if self.windows_monitor:
            self.windows_monitor.stop_monitoring()

        if self.admin_monitor:
            self.admin_monitor.stop_monitoring()

        self.gui.stop()
        print("PowerShell Learner stopped.")


def main():
    """Main entry point"""
    # Check if running on Windows
    if sys.platform != 'win32':
        print("=" * 60)
        print("ERROR: PowerShell Learner only works on Windows!")
        print(f"Current platform: {sys.platform}")
        print("=" * 60)
        sys.exit(1)

    app = PowerShellLearner()

    try:
        app.start()

        # Keep running
        while app.running:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\nShutdown requested by user...")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.stop()


if __name__ == "__main__":
    main()
