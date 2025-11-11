#!/usr/bin/env python3
"""
Windows System Monitor
Continuously monitors system-level events, administrative actions, and registry changes.
Requires: psutil, pywin32, watchdog
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import deque

# Core monitoring libraries
import psutil
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Windows-specific libraries
try:
    import win32evtlog
    import win32evtlogutil
    import win32event
    import win32file
    import win32con
    import win32api
    import win32security
    import winerror
    import pywintypes
    import winreg
    import win32service
    import win32serviceutil
except ImportError as e:
    print(f"Error importing Windows libraries: {e}")
    print("Please install pywin32: pip install pywin32")
    print("This tool only works on Windows systems.")
    sys.exit(1)


class WindowsMonitor:
    """Main monitoring class for Windows system events"""

    def __init__(self, config_file: str = "monitor_config.json"):
        self.config_file = config_file
        self.config = self.load_config()
        self.setup_logging()
        self.running = False
        self.threads = []

        # Event storage with thread lock
        self.events = []
        self.events_lock = threading.Lock()
        self.max_events = self.config.get('max_events', 1000)

        # Batched file writing
        self.unsaved_events = 0
        self.save_batch_size = 10  # Save every 10 events

        # Monitoring components
        self.process_monitor = ProcessMonitor(self)
        self.registry_monitor = RegistryMonitor(self)
        self.file_monitor = FileSystemMonitor(self)
        self.event_log_monitor = EventLogMonitor(self)
        self.network_adapter_monitor = NetworkAdapterMonitor(self)
        self.device_monitor = DeviceMonitor(self)
        self.service_monitor = ServiceMonitor(self)

    def load_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        default_config = {
            "monitoring": {
                "processes": True,
                "registry": True,
                "filesystem": True,
                "event_logs": True,
                "network": True,
                "network_adapters": True,
                "devices": False,  # TODO: Not implemented yet
                "services": True
            },
            "paths_to_watch": [
                "C:\\Windows\\Temp",
                "C:\\Users\\Public"
            ],
            "registry_keys": [
                "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                "HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
                "HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Services"
            ],
            "event_logs": [
                "System",
                "Application"
            ],
            "output_file": "monitor_events.json",
            "log_level": "INFO",
            "max_events": 1000,
            "check_interval": 5
        }

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                print(f"Error loading config: {e}, using defaults")

        # Save default config
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save default config: {e}")

        return default_config

    def setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))

        # Create logger
        self.logger = logging.getLogger('WindowsMonitor')
        self.logger.setLevel(log_level)

        # Avoid duplicate handlers
        if not self.logger.handlers:
            # File handler
            file_handler = logging.FileHandler('windows_monitor.log')
            file_handler.setLevel(log_level)

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)

            # Formatter
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def log_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log and store monitoring events"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'data': event_data
        }

        with self.events_lock:
            self.events.append(event)

            # Maintain max events limit
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

            self.unsaved_events += 1

        # Log to file
        self.logger.info(f"{event_type}: {json.dumps(event_data)}")

        # Batched saving - only save every N events
        if self.unsaved_events >= self.save_batch_size:
            self.save_events()

    def save_events(self):
        """Save events to output file"""
        try:
            output_file = self.config.get('output_file', 'monitor_events.json')
            with self.events_lock:
                with open(output_file, 'w') as f:
                    json.dump(self.events, f, indent=2)
                self.unsaved_events = 0
        except Exception as e:
            self.logger.error(f"Error saving events: {e}")

    def start_monitoring(self):
        """Start all monitoring threads"""
        self.logger.info("Starting Windows system monitoring...")
        self.running = True

        # Start monitoring threads based on configuration
        if self.config['monitoring']['processes']:
            thread = threading.Thread(target=self.process_monitor.monitor, daemon=True, name="ProcessMonitor")
            thread.start()
            self.threads.append(thread)

        if self.config['monitoring']['registry']:
            thread = threading.Thread(target=self.registry_monitor.monitor, daemon=True, name="RegistryMonitor")
            thread.start()
            self.threads.append(thread)

        if self.config['monitoring']['filesystem']:
            thread = threading.Thread(target=self.file_monitor.start_monitoring, daemon=True, name="FileSystemMonitor")
            thread.start()
            self.threads.append(thread)

        if self.config['monitoring']['event_logs']:
            thread = threading.Thread(target=self.event_log_monitor.monitor, daemon=True, name="EventLogMonitor")
            thread.start()
            self.threads.append(thread)

        if self.config['monitoring']['network']:
            thread = threading.Thread(target=self.monitor_network, daemon=True, name="NetworkMonitor")
            thread.start()
            self.threads.append(thread)

        if self.config['monitoring']['network_adapters']:
            thread = threading.Thread(target=self.network_adapter_monitor.monitor, daemon=True, name="NetworkAdapterMonitor")
            thread.start()
            self.threads.append(thread)

        if self.config['monitoring']['devices']:
            thread = threading.Thread(target=self.device_monitor.monitor, daemon=True, name="DeviceMonitor")
            thread.start()
            self.threads.append(thread)

        if self.config['monitoring']['services']:
            thread = threading.Thread(target=self.service_monitor.monitor, daemon=True, name="ServiceMonitor")
            thread.start()
            self.threads.append(thread)

    def stop_monitoring(self):
        """Stop all monitoring"""
        self.logger.info("Stopping monitoring...")
        self.running = False

        # Stop file system observer
        self.file_monitor.stop_monitoring()

        # Wait for threads to finish (with timeout)
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)

        # Final save
        self.save_events()
        self.logger.info("Monitoring stopped.")

    def monitor_network(self):
        """Monitor network connections and changes"""
        previous_connections = set()

        while self.running:
            try:
                current_connections = set()
                for conn in psutil.net_connections(kind='inet'):
                    if conn.status == 'ESTABLISHED' and conn.laddr and conn.raddr:
                        # Properly extract connection info from namedtuples
                        local_addr = f"{conn.laddr.ip}:{conn.laddr.port}"
                        remote_addr = f"{conn.raddr.ip}:{conn.raddr.port}"
                        conn_info = (local_addr, remote_addr, conn.pid)
                        current_connections.add(conn_info)

                # Check for new connections
                new_connections = current_connections - previous_connections
                for local_addr, remote_addr, pid in new_connections:
                    try:
                        process = psutil.Process(pid)
                        self.log_event('NEW_NETWORK_CONNECTION', {
                            'local_address': local_addr,
                            'remote_address': remote_addr,
                            'pid': pid,
                            'process_name': process.name(),
                            'process_exe': process.exe() if process.exe() else 'Unknown'
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                previous_connections = current_connections
                time.sleep(self.config.get('check_interval', 5))

            except Exception as e:
                self.logger.error(f"Network monitoring error: {e}")
                time.sleep(10)


class ProcessMonitor:
    """Monitor process creation, termination, and changes"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.previous_processes = {}

    def monitor(self):
        """Monitor process changes"""
        while self.main_monitor.running:
            try:
                current_processes = {}

                for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'create_time', 'ppid']):
                    try:
                        info = proc.info
                        pid = info['pid']
                        current_processes[pid] = info

                        # Check for new processes
                        if pid not in self.previous_processes:
                            self.main_monitor.log_event('PROCESS_CREATED', {
                                'pid': pid,
                                'name': info['name'],
                                'exe': info['exe'],
                                'cmdline': ' '.join(info['cmdline']) if info['cmdline'] else '',
                                'ppid': info['ppid'],
                                'create_time': info['create_time']
                            })

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Check for terminated processes
                terminated_pids = set(self.previous_processes.keys()) - set(current_processes.keys())
                for pid in terminated_pids:
                    proc_info = self.previous_processes[pid]
                    self.main_monitor.log_event('PROCESS_TERMINATED', {
                        'pid': pid,
                        'name': proc_info['name'],
                        'exe': proc_info['exe']
                    })

                self.previous_processes = current_processes
                time.sleep(self.main_monitor.config.get('check_interval', 5))

            except Exception as e:
                self.main_monitor.logger.error(f"Process monitoring error: {e}")
                time.sleep(10)


class RegistryMonitor:
    """Monitor Windows registry changes"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.registry_snapshots = {}

    def get_registry_values(self, key_path: str) -> Dict[str, Any]:
        """Get all values from a registry key"""
        values = {}
        try:
            # Parse key path
            if key_path.startswith('HKEY_LOCAL_MACHINE'):
                root_key = winreg.HKEY_LOCAL_MACHINE
                subkey_path = key_path.replace('HKEY_LOCAL_MACHINE\\', '')
            elif key_path.startswith('HKEY_CURRENT_USER'):
                root_key = winreg.HKEY_CURRENT_USER
                subkey_path = key_path.replace('HKEY_CURRENT_USER\\', '')
            else:
                return values

            # Open registry key
            key = None
            try:
                key = winreg.OpenKey(root_key, subkey_path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, value_type = winreg.EnumValue(key, i)
                        values[name] = {'value': value, 'type': value_type}
                        i += 1
                    except OSError:
                        break
            finally:
                if key:
                    winreg.CloseKey(key)

        except Exception as e:
            self.main_monitor.logger.debug(f"Error reading registry key {key_path}: {e}")

        return values

    def monitor(self):
        """Monitor registry changes"""
        # Take initial snapshots
        for key_path in self.main_monitor.config['registry_keys']:
            self.registry_snapshots[key_path] = self.get_registry_values(key_path)

        while self.main_monitor.running:
            try:
                for key_path in self.main_monitor.config['registry_keys']:
                    current_values = self.get_registry_values(key_path)
                    previous_values = self.registry_snapshots.get(key_path, {})

                    # Check for new/modified values
                    for name, data in current_values.items():
                        if name not in previous_values:
                            self.main_monitor.log_event('REGISTRY_VALUE_ADDED', {
                                'key_path': key_path,
                                'value_name': name,
                                'value_data': str(data['value']),
                                'value_type': data['type']
                            })
                        elif previous_values[name]['value'] != data['value']:
                            self.main_monitor.log_event('REGISTRY_VALUE_MODIFIED', {
                                'key_path': key_path,
                                'value_name': name,
                                'old_value': str(previous_values[name]['value']),
                                'new_value': str(data['value']),
                                'value_type': data['type']
                            })

                    # Check for deleted values
                    for name in previous_values:
                        if name not in current_values:
                            self.main_monitor.log_event('REGISTRY_VALUE_DELETED', {
                                'key_path': key_path,
                                'value_name': name,
                                'old_value': str(previous_values[name]['value'])
                            })

                    # Update snapshot
                    self.registry_snapshots[key_path] = current_values

                time.sleep(self.main_monitor.config.get('check_interval', 5))

            except Exception as e:
                self.main_monitor.logger.error(f"Registry monitoring error: {e}")
                time.sleep(10)


class FileSystemMonitor:
    """Monitor file system events using watchdog"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.observer = Observer()
        self.event_handler = FileSystemEventHandler()
        self.setup_event_handler()

    def setup_event_handler(self):
        """Setup file system event handlers"""

        def on_created(event):
            self.main_monitor.log_event('FILE_CREATED', {
                'path': event.src_path,
                'is_directory': event.is_directory
            })

        def on_deleted(event):
            self.main_monitor.log_event('FILE_DELETED', {
                'path': event.src_path,
                'is_directory': event.is_directory
            })

        def on_modified(event):
            if not event.is_directory:  # Skip directory modifications
                self.main_monitor.log_event('FILE_MODIFIED', {
                    'path': event.src_path,
                    'is_directory': event.is_directory
                })

        def on_moved(event):
            self.main_monitor.log_event('FILE_MOVED', {
                'src_path': event.src_path,
                'dest_path': event.dest_path,
                'is_directory': event.is_directory
            })

        self.event_handler.on_created = on_created
        self.event_handler.on_deleted = on_deleted
        self.event_handler.on_modified = on_modified
        self.event_handler.on_moved = on_moved

    def start_monitoring(self):
        """Start file system monitoring"""
        try:
            for path in self.main_monitor.config['paths_to_watch']:
                if os.path.exists(path):
                    self.observer.schedule(self.event_handler, path, recursive=True)
                    self.main_monitor.logger.info(f"Monitoring file system path: {path}")
                else:
                    self.main_monitor.logger.warning(f"Path does not exist, skipping: {path}")

            self.observer.start()

            # Keep the monitoring thread alive
            while self.main_monitor.running:
                time.sleep(1)

        except Exception as e:
            self.main_monitor.logger.error(f"File system monitoring error: {e}")

    def stop_monitoring(self):
        """Stop file system monitoring"""
        try:
            if self.observer.is_alive():
                self.observer.stop()
                self.observer.join(timeout=2.0)
        except Exception as e:
            self.main_monitor.logger.error(f"Error stopping file system monitor: {e}")


class EventLogMonitor:
    """Monitor Windows Event Logs"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.last_record_numbers = {}

    def monitor(self):
        """Monitor Windows event logs"""
        # Initialize last record numbers
        for log_name in self.main_monitor.config['event_logs']:
            try:
                handle = win32evtlog.OpenEventLog(None, log_name)
                total_records = win32evtlog.GetNumberOfEventLogRecords(handle)
                self.last_record_numbers[log_name] = total_records
                win32evtlog.CloseEventLog(handle)
            except Exception as e:
                self.main_monitor.logger.error(f"Error initializing event log {log_name}: {e}")

        while self.main_monitor.running:
            try:
                for log_name in self.main_monitor.config['event_logs']:
                    self.check_event_log(log_name)

                time.sleep(self.main_monitor.config.get('check_interval', 5))

            except Exception as e:
                self.main_monitor.logger.error(f"Event log monitoring error: {e}")
                time.sleep(10)

    def check_event_log(self, log_name: str):
        """Check for new events in a specific log"""
        handle = None
        try:
            handle = win32evtlog.OpenEventLog(None, log_name)
            total_records = win32evtlog.GetNumberOfEventLogRecords(handle)
            last_checked = self.last_record_numbers.get(log_name, 0)

            if total_records > last_checked:
                # Read new events
                events_to_read = min(100, total_records - last_checked)
                events = win32evtlog.ReadEventLog(
                    handle,
                    win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ,
                    0
                )

                for event in events[-events_to_read:]:
                    try:
                        # Extract relevant event information
                        event_data = {
                            'log_name': log_name,
                            'record_number': event.RecordNumber,
                            'event_id': event.EventID & 0xFFFF,  # Mask to get actual event ID
                            'event_type': event.EventType,
                            'time_generated': event.TimeGenerated.isoformat(),
                            'source_name': event.SourceName,
                            'computer_name': event.ComputerName,
                            'sid': str(event.Sid) if event.Sid else None
                        }

                        # Try to get event message
                        try:
                            event_data['message'] = win32evtlogutil.SafeFormatMessage(event, log_name)
                        except Exception as e:
                            event_data['message'] = f'Unable to format message: {str(e)}'

                        self.main_monitor.log_event('WINDOWS_EVENT_LOG', event_data)

                    except Exception as e:
                        self.main_monitor.logger.debug(f"Error processing event log entry: {e}")

                self.last_record_numbers[log_name] = total_records

        except Exception as e:
            self.main_monitor.logger.error(f"Error checking event log {log_name}: {e}")
        finally:
            if handle:
                try:
                    win32evtlog.CloseEventLog(handle)
                except:
                    pass


class NetworkAdapterMonitor:
    """Monitor network adapter changes"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.previous_adapters = {}

    def monitor(self):
        """Monitor network adapter changes"""
        while self.main_monitor.running:
            try:
                # FIX: psutil.net_if_addrs() returns a dict, not a list
                current_adapters = {}
                net_if_addrs = psutil.net_if_addrs()

                for name, addrs in net_if_addrs.items():
                    current_adapters[name] = addrs

                # Check for new adapters
                for name, addrs in current_adapters.items():
                    if name not in self.previous_adapters:
                        self.main_monitor.log_event('NETWORK_ADAPTER_ADDED', {
                            'name': name,
                            'addresses': [addr.address for addr in addrs]
                        })

                # Check for removed adapters
                for name in set(self.previous_adapters) - set(current_adapters):
                    self.main_monitor.log_event('NETWORK_ADAPTER_REMOVED', {
                        'name': name
                    })

                self.previous_adapters = current_adapters
                time.sleep(self.main_monitor.config.get('check_interval', 5))

            except Exception as e:
                self.main_monitor.logger.error(f"Network adapter monitoring error: {e}")
                time.sleep(10)


class DeviceMonitor:
    """Monitor device connections and disconnections"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor

    def monitor(self):
        """Monitor device changes"""
        while self.main_monitor.running:
            try:
                # TODO: Implement device monitoring logic using WMI or win32com
                time.sleep(self.main_monitor.config.get('check_interval', 5))

            except Exception as e:
                self.main_monitor.logger.error(f"Device monitoring error: {e}")
                time.sleep(10)


class ServiceMonitor:
    """Monitor service start/stop events"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.previous_states = {}

    def monitor(self):
        """Monitor service changes"""
        while self.main_monitor.running:
            hscm = None
            try:
                # FIX: Properly manage SC Manager handle
                hscm = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
                services = win32service.EnumServicesStatus(
                    hscm,
                    win32service.SERVICE_WIN32,
                    win32service.SERVICE_STATE_ALL
                )

                for service in services:
                    name, display_name, status = service
                    current_state = status[1]

                    if name in self.previous_states:
                        if current_state != self.previous_states[name]:
                            state_names = {
                                1: "STOPPED",
                                2: "START_PENDING",
                                3: "STOP_PENDING",
                                4: "RUNNING",
                                5: "CONTINUE_PENDING",
                                6: "PAUSE_PENDING",
                                7: "PAUSED"
                            }

                            self.main_monitor.log_event('SERVICE_STATUS_CHANGED', {
                                'name': name,
                                'display_name': display_name,
                                'old_status': state_names.get(self.previous_states[name], "UNKNOWN"),
                                'new_status': state_names.get(current_state, "UNKNOWN"),
                                'status_code': current_state
                            })

                    self.previous_states[name] = current_state

                time.sleep(self.main_monitor.config.get('check_interval', 5))

            except Exception as e:
                self.main_monitor.logger.error(f"Service monitoring error: {e}")
                time.sleep(10)
            finally:
                if hscm:
                    try:
                        win32service.CloseServiceHandle(hscm)
                    except:
                        pass


def main():
    """Main function to run the Windows monitor"""
    # Check if running on Windows
    if sys.platform != 'win32':
        print("ERROR: This tool only works on Windows systems!")
        print(f"Current platform: {sys.platform}")
        sys.exit(1)

    print("Windows System Monitor")
    print("=" * 50)

    # Create monitor instance
    monitor = WindowsMonitor()

    try:
        # Start monitoring
        monitor.start_monitoring()

        print("Monitoring started. Press Ctrl+C to stop...")
        print(f"Events will be saved to: {monitor.config.get('output_file', 'monitor_events.json')}")
        print(f"Log file: windows_monitor.log")

        # Keep main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop_monitoring()
        print("Monitor stopped.")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()
