#!/usr/bin/env python3
"""
Extended Monitors for PowerShell Learner
Additional monitoring capabilities for Windows system actions.

Monitors:
- Windows Firewall rules
- Scheduled Tasks
- Windows Features
- Group Policy changes
- System environment variables
- Printer configuration
"""

import logging
import time
import subprocess
from typing import Dict, Any, List
from datetime import datetime

try:
    import win32api
    import win32con
    import win32security
except ImportError:
    print("WARNING: pywin32 not available. Extended monitors will not work.")


logger = logging.getLogger(__name__)


class FirewallMonitor:
    """Monitor Windows Firewall rule changes"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.previous_rules = {}

    def monitor(self):
        """Monitor firewall changes"""
        while self.main_monitor.running:
            try:
                current_rules = self._get_firewall_rules()

                # Check for new rules
                for rule_name, rule_data in current_rules.items():
                    if rule_name not in self.previous_rules:
                        self.main_monitor.log_event('FIREWALL_RULE_ADDED', {
                            'rule_name': rule_name,
                            'enabled': rule_data.get('enabled', 'Unknown'),
                            'direction': rule_data.get('direction', 'Unknown'),
                            'action': rule_data.get('action', 'Unknown')
                        })

                # Check for removed rules
                for rule_name in set(self.previous_rules) - set(current_rules):
                    self.main_monitor.log_event('FIREWALL_RULE_REMOVED', {
                        'rule_name': rule_name
                    })

                self.previous_rules = current_rules
                time.sleep(self.main_monitor.config.get('check_interval', 10))

            except Exception as e:
                logger.error(f"Firewall monitoring error: {e}")
                time.sleep(30)

    def _get_firewall_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get current firewall rules using netsh"""
        rules = {}

        try:
            # Use PowerShell to get firewall rules (more reliable than netsh)
            cmd = ['powershell', '-Command',
                   'Get-NetFirewallRule | Select-Object -First 50 Name,Enabled,Direction,Action | ConvertTo-Json']

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout:
                import json
                rules_data = json.loads(result.stdout)

                if not isinstance(rules_data, list):
                    rules_data = [rules_data]

                for rule in rules_data:
                    if isinstance(rule, dict):
                        name = rule.get('Name', '')
                        if name:
                            rules[name] = {
                                'enabled': rule.get('Enabled', 'Unknown'),
                                'direction': rule.get('Direction', 'Unknown'),
                                'action': rule.get('Action', 'Unknown')
                            }

        except Exception as e:
            logger.debug(f"Error getting firewall rules: {e}")

        return rules


class ScheduledTaskMonitor:
    """Monitor Windows Scheduled Tasks"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.previous_tasks = {}

    def monitor(self):
        """Monitor scheduled task changes"""
        while self.main_monitor.running:
            try:
                current_tasks = self._get_scheduled_tasks()

                # Check for new tasks
                for task_name, task_data in current_tasks.items():
                    if task_name not in self.previous_tasks:
                        self.main_monitor.log_event('SCHEDULED_TASK_CREATED', {
                            'task_name': task_name,
                            'state': task_data.get('state', 'Unknown'),
                            'next_run': task_data.get('next_run', 'Unknown')
                        })

                # Check for removed tasks
                for task_name in set(self.previous_tasks) - set(current_tasks):
                    self.main_monitor.log_event('SCHEDULED_TASK_DELETED', {
                        'task_name': task_name
                    })

                # Check for state changes
                for task_name in set(current_tasks) & set(self.previous_tasks):
                    if current_tasks[task_name]['state'] != self.previous_tasks[task_name]['state']:
                        self.main_monitor.log_event('SCHEDULED_TASK_STATE_CHANGED', {
                            'task_name': task_name,
                            'old_state': self.previous_tasks[task_name]['state'],
                            'new_state': current_tasks[task_name]['state']
                        })

                self.previous_tasks = current_tasks
                time.sleep(self.main_monitor.config.get('check_interval', 15))

            except Exception as e:
                logger.error(f"Scheduled task monitoring error: {e}")
                time.sleep(30)

    def _get_scheduled_tasks(self) -> Dict[str, Dict[str, Any]]:
        """Get current scheduled tasks"""
        tasks = {}

        try:
            cmd = ['powershell', '-Command',
                   'Get-ScheduledTask | Select-Object -First 30 TaskName,State | ConvertTo-Json']

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout:
                import json
                tasks_data = json.loads(result.stdout)

                if not isinstance(tasks_data, list):
                    tasks_data = [tasks_data]

                for task in tasks_data:
                    if isinstance(task, dict):
                        name = task.get('TaskName', '')
                        if name:
                            tasks[name] = {
                                'state': str(task.get('State', 'Unknown')),
                                'next_run': 'Unknown'  # Would need more complex query
                            }

        except Exception as e:
            logger.debug(f"Error getting scheduled tasks: {e}")

        return tasks


class EnvironmentVariableMonitor:
    """Monitor system environment variable changes"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.previous_env_vars = {}

    def monitor(self):
        """Monitor environment variable changes"""
        while self.main_monitor.running:
            try:
                current_env_vars = self._get_system_env_vars()

                # Check for new/modified variables
                for var_name, var_value in current_env_vars.items():
                    if var_name not in self.previous_env_vars:
                        self.main_monitor.log_event('ENV_VAR_ADDED', {
                            'variable_name': var_name,
                            'value': var_value[:100]  # Limit length
                        })
                    elif self.previous_env_vars[var_name] != var_value:
                        self.main_monitor.log_event('ENV_VAR_MODIFIED', {
                            'variable_name': var_name,
                            'old_value': self.previous_env_vars[var_name][:100],
                            'new_value': var_value[:100]
                        })

                # Check for removed variables
                for var_name in set(self.previous_env_vars) - set(current_env_vars):
                    self.main_monitor.log_event('ENV_VAR_DELETED', {
                        'variable_name': var_name,
                        'old_value': self.previous_env_vars[var_name][:100]
                    })

                self.previous_env_vars = current_env_vars
                time.sleep(self.main_monitor.config.get('check_interval', 20))

            except Exception as e:
                logger.error(f"Environment variable monitoring error: {e}")
                time.sleep(30)

    def _get_system_env_vars(self) -> Dict[str, str]:
        """Get system environment variables from registry"""
        env_vars = {}

        try:
            import winreg
            key = None
            try:
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
                    0,
                    winreg.KEY_READ
                )

                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        env_vars[name] = str(value)
                        i += 1
                    except OSError:
                        break

            finally:
                if key:
                    winreg.CloseKey(key)

        except Exception as e:
            logger.debug(f"Error reading environment variables: {e}")

        return env_vars


class WindowsFeatureMonitor:
    """Monitor Windows optional features"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.previous_features = {}

    def monitor(self):
        """Monitor Windows feature changes"""
        while self.main_monitor.running:
            try:
                current_features = self._get_windows_features()

                # Check for state changes
                for feature_name, feature_state in current_features.items():
                    if feature_name in self.previous_features:
                        if self.previous_features[feature_name] != feature_state:
                            self.main_monitor.log_event('WINDOWS_FEATURE_CHANGED', {
                                'feature_name': feature_name,
                                'old_state': self.previous_features[feature_name],
                                'new_state': feature_state
                            })
                    else:
                        # New feature detected (rare, but possible)
                        self.main_monitor.log_event('WINDOWS_FEATURE_DETECTED', {
                            'feature_name': feature_name,
                            'state': feature_state
                        })

                self.previous_features = current_features
                time.sleep(self.main_monitor.config.get('check_interval', 30))

            except Exception as e:
                logger.error(f"Windows feature monitoring error: {e}")
                time.sleep(60)

    def _get_windows_features(self) -> Dict[str, str]:
        """Get Windows optional features"""
        features = {}

        try:
            # Use DISM to query features
            cmd = ['powershell', '-Command',
                   'Get-WindowsOptionalFeature -Online | Select-Object -First 20 FeatureName,State | ConvertTo-Json']

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0 and result.stdout:
                import json
                features_data = json.loads(result.stdout)

                if not isinstance(features_data, list):
                    features_data = [features_data]

                for feature in features_data:
                    if isinstance(feature, dict):
                        name = feature.get('FeatureName', '')
                        state = str(feature.get('State', 'Unknown'))
                        if name:
                            features[name] = state

        except Exception as e:
            logger.debug(f"Error getting Windows features: {e}")

        return features


class PrinterMonitor:
    """Monitor printer configuration changes"""

    def __init__(self, main_monitor):
        self.main_monitor = main_monitor
        self.previous_printers = {}

    def monitor(self):
        """Monitor printer changes"""
        while self.main_monitor.running:
            try:
                current_printers = self._get_printers()

                # Check for new printers
                for printer_name in set(current_printers) - set(self.previous_printers):
                    self.main_monitor.log_event('PRINTER_ADDED', {
                        'printer_name': printer_name,
                        'driver': current_printers[printer_name].get('driver', 'Unknown')
                    })

                # Check for removed printers
                for printer_name in set(self.previous_printers) - set(current_printers):
                    self.main_monitor.log_event('PRINTER_REMOVED', {
                        'printer_name': printer_name
                    })

                self.previous_printers = current_printers
                time.sleep(self.main_monitor.config.get('check_interval', 15))

            except Exception as e:
                logger.error(f"Printer monitoring error: {e}")
                time.sleep(30)

    def _get_printers(self) -> Dict[str, Dict[str, str]]:
        """Get installed printers"""
        printers = {}

        try:
            cmd = ['powershell', '-Command',
                   'Get-Printer | Select-Object Name,DriverName | ConvertTo-Json']

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0 and result.stdout:
                import json
                printers_data = json.loads(result.stdout)

                if not isinstance(printers_data, list):
                    printers_data = [printers_data]

                for printer in printers_data:
                    if isinstance(printer, dict):
                        name = printer.get('Name', '')
                        if name:
                            printers[name] = {
                                'driver': printer.get('DriverName', 'Unknown')
                            }

        except Exception as e:
            logger.debug(f"Error getting printers: {e}")

        return printers


# Export all monitor classes
__all__ = [
    'FirewallMonitor',
    'ScheduledTaskMonitor',
    'EnvironmentVariableMonitor',
    'WindowsFeatureMonitor',
    'PrinterMonitor'
]
