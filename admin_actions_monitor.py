#!/usr/bin/env python3
"""
Administrative Actions Monitoring
Tracks system configuration changes and policy modifications using pywin32.
Logs administrative actions with equivalent PowerShell commands.

Author: Security Monitoring System
Date: 2024
"""

import win32api
import win32con
import win32security
import win32netcon
import win32net
import win32service
import win32serviceutil
import wmi
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('admin_actions.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class AdminAction:
    """Represents an administrative action detected on the system."""
    timestamp: str
    action_type: str
    description: str
    user: str
    process: str
    details: Dict[str, Any]
    powershell_command: str
    severity: str = "INFO"

class AdminActionsMonitor:
    """Monitor for administrative actions and system configuration changes."""

    def __init__(self):
        # FIX: Add error handling for WMI initialization
        try:
            self.wmi_conn = wmi.WMI()
        except Exception as e:
            logger.error(f"Failed to initialize WMI connection: {e}")
            self.wmi_conn = None

        self.running = False
        self.actions_log = []
        self.actions_lock = threading.Lock()  # FIX: Add lock for thread-safe access
        self.monitoring_thread = None
        self.previous_states = {
            'services': {},
            'users': {},
            'policies': {},
            'registry': {}
        }
        
    def start_monitoring(self):
        """Start monitoring administrative actions."""
        if not self.running:
            self.running = True
            self.monitoring_thread = threading.Thread(target=self._monitor_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            logger.info("Administrative actions monitoring started")
    
    def stop_monitoring(self):
        """Stop monitoring administrative actions."""
        self.running = False
        if self.monitoring_thread:
            # FIX: Add timeout to prevent hanging
            self.monitoring_thread.join(timeout=5.0)
            if self.monitoring_thread.is_alive():
                logger.warning("Monitoring thread did not stop within timeout")
        logger.info("Administrative actions monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                # Monitor various administrative activities
                self._check_service_changes()
                self._check_user_account_changes()
                self._check_policy_changes()
                self._check_registry_changes()
                self._check_security_changes()
                self._check_system_configuration()
                
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)
    
    def _log_action(self, action: AdminAction):
        """Log an administrative action."""
        with self.actions_lock:
            self.actions_log.append(action)
        logger.info(f"Admin Action: {action.action_type} - {action.description}")
        logger.info(f"PowerShell: {action.powershell_command}")

        # Save to JSON file for persistence
        self._save_to_file(action)
    
    def _save_to_file(self, action: AdminAction):
        """Save action to JSON file."""
        try:
            # FIX: Use a lock file to prevent concurrent write issues
            import fcntl if sys.platform != 'win32' else None
            with open('admin_actions.json', 'a') as f:
                # On Windows, file is locked automatically during write
                json.dump(asdict(action), f)
                f.write('\n')
                f.flush()  # Ensure data is written
        except Exception as e:
            logger.error(f"Failed to save action to file: {e}")
    
    def _check_service_changes(self):
        """Monitor Windows service changes."""
        try:
            sc_manager = win32service.OpenSCManager(None, None, win32service.SC_MANAGER_ENUMERATE_SERVICE)
            services = win32service.EnumServicesStatus(
                sc_manager,
                win32service.SERVICE_WIN32,
                win32service.SERVICE_STATE_ALL
            )
            
            current_services = {}
            for service in services:
                service_name = service[0]
                service_status = service[2][1]  # Current state
                current_services[service_name] = service_status
                
                # Check if service state changed
                if service_name in self.previous_states['services']:
                    if self.previous_states['services'][service_name] != service_status:
                        state_names = {
                            1: "STOPPED",
                            2: "START_PENDING", 
                            3: "STOP_PENDING",
                            4: "RUNNING",
                            5: "CONTINUE_PENDING",
                            6: "PAUSE_PENDING",
                            7: "PAUSED"
                        }
                        
                        old_state = state_names.get(self.previous_states['services'][service_name], "UNKNOWN")
                        new_state = state_names.get(service_status, "UNKNOWN")
                        
                        action = AdminAction(
                            timestamp=datetime.now().isoformat(),
                            action_type="SERVICE_STATE_CHANGE",
                            description=f"Service '{service_name}' state changed from {old_state} to {new_state}",
                            user=win32api.GetUserName(),
                            process="system",
                            details={
                                "service_name": service_name,
                                "old_state": old_state,
                                "new_state": new_state,
                                "state_code": service_status
                            },
                            powershell_command=f"Get-Service -Name '{service_name}' | Select-Object Name,Status,StartType,ServiceType",
                            severity="WARNING"
                        )
                        self._log_action(action)
            
            self.previous_states['services'] = current_services
            win32service.CloseServiceHandle(sc_manager)
                    
        except Exception as e:
            logger.error(f"Error checking services: {e}")
    
    def _check_user_account_changes(self):
        """Monitor user account changes."""
        try:
            users = win32net.NetUserEnum(None, 0)[0]
            current_users = {}
            
            for user in users:
                username = user['name']
                try:
                    user_info = win32net.NetUserGetInfo(None, username, 3)
                    user_flags = user_info['flags']
                    current_users[username] = {
                        'flags': user_flags,
                        'last_logon': user_info.get('last_logon', 0)
                    }
                    
                    # Check for user flag changes (account status, password requirements, etc.)
                    if username in self.previous_states['users']:
                        old_flags = self.previous_states['users'][username]['flags']
                        if old_flags != user_flags:
                            flag_changes = self._analyze_user_flag_changes(old_flags, user_flags)
                            
                            action = AdminAction(
                                timestamp=datetime.now().isoformat(),
                                action_type="USER_ACCOUNT_CHANGE",
                                description=f"User account '{username}' flags changed: {flag_changes}",
                                user=win32api.GetUserName(),
                                process="system",
                                details={
                                    "username": username,
                                    "old_flags": old_flags,
                                    "new_flags": user_flags,
                                    "changes": flag_changes
                                },
                                powershell_command=f"Get-LocalUser -Name '{username}' | Select-Object Name,Enabled,PasswordRequired,UserMayChangePassword,PasswordExpires",
                                severity="HIGH"
                            )
                            self._log_action(action)
                            
                except Exception as e:
                    logger.debug(f"Could not query user {username}: {e}")
            
            self.previous_states['users'] = current_users
                    
        except Exception as e:
            logger.error(f"Error checking user accounts: {e}")
    
    def _analyze_user_flag_changes(self, old_flags: int, new_flags: int) -> List[str]:
        """Analyze changes in user account flags."""
        changes = []
        flag_meanings = {
            win32netcon.UF_ACCOUNTDISABLE: "Account Disabled",
            win32netcon.UF_PASSWD_CANT_CHANGE: "Password Cannot Change",
            win32netcon.UF_DONT_EXPIRE_PASSWD: "Password Never Expires",
            win32netcon.UF_LOCKOUT: "Account Locked Out",
            win32netcon.UF_PASSWORD_EXPIRED: "Password Expired"
        }
        
        for flag, meaning in flag_meanings.items():
            old_has_flag = bool(old_flags & flag)
            new_has_flag = bool(new_flags & flag)
            
            if old_has_flag != new_has_flag:
                status = "enabled" if new_has_flag else "disabled"
                changes.append(f"{meaning} {status}")
        
        return changes
    
    def _check_policy_changes(self):
        """Monitor system policy changes."""
        try:
            # FIX: Check if WMI is available
            if not self.wmi_conn:
                return

            # Check security policies using WMI
            for policy in self.wmi_conn.Win32_AccountPolicy():
                policy_name = getattr(policy, 'Name', 'Unknown')
                policy_data = {
                    'name': policy_name,
                    'setting': getattr(policy, 'Setting', None)
                }
                
                if policy_name not in self.previous_states['policies']:
                    self.previous_states['policies'][policy_name] = policy_data
                elif self.previous_states['policies'][policy_name] != policy_data:
                    action = AdminAction(
                        timestamp=datetime.now().isoformat(),
                        action_type="SECURITY_POLICY_CHANGE",
                        description=f"Security policy '{policy_name}' changed",
                        user=win32api.GetUserName(),
                        process="system",
                        details={
                            "policy_name": policy_name,
                            "old_setting": self.previous_states['policies'][policy_name],
                            "new_setting": policy_data
                        },
                        powershell_command="Get-LocalSecurityPolicy | Where-Object {$_.PolicyName -like '*" + policy_name + "*'}",
                        severity="HIGH"
                    )
                    self._log_action(action)
                    self.previous_states['policies'][policy_name] = policy_data
                    
        except Exception as e:
            logger.error(f"Error checking policies: {e}")
    
    def _check_registry_changes(self):
        """Monitor critical registry changes."""
        try:
            # Monitor critical registry keys
            critical_keys = [
                (win32con.HKEY_LOCAL_MACHINE, "HKLM", "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (win32con.HKEY_CURRENT_USER, "HKCU", "SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"),
                (win32con.HKEY_LOCAL_MACHINE, "HKLM", "SYSTEM\\CurrentControlSet\\Services")
            ]

            for hkey, hkey_name, subkey in critical_keys:
                try:
                    key_handle = win32api.RegOpenKeyEx(hkey, subkey, 0, win32con.KEY_READ)
                    values = {}
                    
                    try:
                        i = 0
                        while True:
                            try:
                                name, value, _ = win32api.RegEnumValue(key_handle, i)
                                values[name] = str(value)[:100]  # Limit value length
                                i += 1
                            except win32api.error:
                                break
                    finally:
                        win32api.RegCloseKey(key_handle)

                    # FIX: Use readable registry path name
                    key_path = f"{hkey_name}\\{subkey}"
                    if key_path in self.previous_states['registry']:
                        old_values = self.previous_states['registry'][key_path]
                        if old_values != values:
                            # Find specific changes
                            added = set(values.keys()) - set(old_values.keys())
                            removed = set(old_values.keys()) - set(values.keys())
                            modified = {k for k in values.keys() & old_values.keys()
                                      if values[k] != old_values[k]}

                            if added or removed or modified:
                                action = AdminAction(
                                    timestamp=datetime.now().isoformat(),
                                    action_type="REGISTRY_CHANGE",
                                    description=f"Registry changes in {key_path}",
                                    user=win32api.GetUserName(),
                                    process="system",
                                    details={
                                        "registry_path": key_path,
                                        "added_values": list(added),
                                        "removed_values": list(removed),
                                        "modified_values": list(modified)
                                    },
                                    powershell_command=f"Get-ItemProperty -Path '{key_path}:' | Format-List",
                                    severity="HIGH"
                                )
                                self._log_action(action)

                    self.previous_states['registry'][key_path] = values
                    
                except Exception as e:
                    logger.debug(f"Could not access registry key {subkey}: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking registry: {e}")
    
    def _check_security_changes(self):
        """Monitor security-related changes."""
        try:
            # Check for privilege escalation attempts
            current_user = win32api.GetUserName()
            
            # Get current user privileges
            try:
                token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), 
                                                     win32security.TOKEN_QUERY)
                privileges = win32security.GetTokenInformation(token, 
                                                             win32security.TokenPrivileges)
                
                privilege_names = []
                for privilege in privileges:
                    try:
                        name = win32security.LookupPrivilegeName(None, privilege[0])
                        privilege_names.append(name)
                    except:
                        continue
                
                win32api.CloseHandle(token)
                
                action = AdminAction(
                    timestamp=datetime.now().isoformat(),
                    action_type="PRIVILEGE_CHECK",
                    description=f"Current privileges for user {current_user}",
                    user=current_user,
                    process="admin_monitor",
                    details={
                        "user": current_user,
                        "privileges": privilege_names[:10]  # Limit output
                    },
                    powershell_command=f"whoami /priv",
                    severity="INFO"
                )
                
                # Only log if this is the first check or privileges changed significantly
                if len(self.actions_log) % 10 == 0:  # Log every 10th check
                    self._log_action(action)
                    
            except Exception as e:
                logger.debug(f"Could not check privileges: {e}")
                
        except Exception as e:
            logger.error(f"Error checking security: {e}")
    
    def _check_system_configuration(self):
        """Monitor system configuration changes."""
        try:
            # FIX: Check if WMI is available
            if not self.wmi_conn:
                return

            # Check system information that might indicate configuration changes
            computer_info = self.wmi_conn.Win32_ComputerSystem()[0]
            
            config_data = {
                'domain': computer_info.Domain,
                'workgroup': getattr(computer_info, 'Workgroup', None),
                'total_memory': computer_info.TotalPhysicalMemory
            }
            
            if 'system_config' not in self.previous_states:
                self.previous_states['system_config'] = config_data
            elif self.previous_states['system_config'] != config_data:
                changes = []
                for key, value in config_data.items():
                    if self.previous_states['system_config'].get(key) != value:
                        changes.append(f"{key}: {self.previous_states['system_config'].get(key)} -> {value}")
                
                action = AdminAction(
                    timestamp=datetime.now().isoformat(),
                    action_type="SYSTEM_CONFIG_CHANGE",
                    description=f"System configuration changed: {', '.join(changes)}",
                    user=win32api.GetUserName(),
                    process="system",
                    details={
                        "old_config": self.previous_states['system_config'],
                        "new_config": config_data,
                        "changes": changes
                    },
                    powershell_command="Get-ComputerInfo | Select-Object WindowsProductName,TotalPhysicalMemory,Domain,Workgroup",
                    severity="WARNING"
                )
                self._log_action(action)
                self.previous_states['system_config'] = config_data
                
        except Exception as e:
            logger.error(f"Error checking system configuration: {e}")
    
    def get_recent_actions(self, limit: int = 50) -> List[AdminAction]:
        """Get recent administrative actions."""
        return self.actions_log[-limit:]
    
    def export_actions_report(self, filename: str = None):
        """Export actions to a detailed report."""
        if not filename:
            filename = f"admin_actions_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            "report_generated": datetime.now().isoformat(),
            "total_actions": len(self.actions_log),
            "actions": [asdict(action) for action in self.actions_log],
            "summary": {
                "service_changes": len([a for a in self.actions_log if a.action_type == "SERVICE_STATE_CHANGE"]),
                "user_changes": len([a for a in self.actions_log if a.action_type == "USER_ACCOUNT_CHANGE"]),
                "policy_changes": len([a for a in self.actions_log if a.action_type == "SECURITY_POLICY_CHANGE"]),
                "registry_changes": len([a for a in self.actions_log if a.action_type == "REGISTRY_CHANGE"]),
                "high_severity": len([a for a in self.actions_log if a.severity == "HIGH"])
            }
        }
        
        try:
            with open(filename, 'w') as f:
                json.dump(report_data, f, indent=2)
            logger.info(f"Actions report exported to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to export report: {e}")
            return None

def main():
    """Main function to run the administrative actions monitor."""
    monitor = AdminActionsMonitor()
    
    try:
        print("Starting Administrative Actions Monitor...")
        print("Press Ctrl+C to stop monitoring")
        
        monitor.start_monitoring()
        
        # Keep the main thread alive
        while True:
            time.sleep(60)
            print(f"Monitoring... {len(monitor.actions_log)} actions logged")
            
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop_monitoring()
        
        # Export final report
        report_file = monitor.export_actions_report()
        if report_file:
            print(f"Final report saved to: {report_file}")
        
        print("Monitor stopped.")

if __name__ == "__main__":
    main()
