#!/usr/bin/env python3
"""
Test script for Administrative Actions Monitoring
Demonstrates the monitoring capabilities and generates sample events.
"""

import sys
import time
from admin_actions_monitor import AdminActionsMonitor, AdminAction
from datetime import datetime

def test_monitoring():
    """Test the administrative actions monitoring system."""
    print("Testing Administrative Actions Monitoring System")
    print("=" * 50)
    
    # Create monitor instance
    monitor = AdminActionsMonitor()
    
    # Test 1: Basic functionality
    print("\n1. Testing basic monitoring setup...")
    monitor.start_monitoring()
    
    # Let it run for a short time
    print("   Monitoring for 30 seconds...")
    time.sleep(30)
    
    # Test 2: Manual action logging
    print("\n2. Testing manual action logging...")
    test_action = AdminAction(
        timestamp=datetime.now().isoformat(),
        action_type="TEST_ACTION",
        description="Manual test action for demonstration",
        user="test_user",
        process="test_process",
        details={
            "test_parameter": "test_value",
            "action_count": 1
        },
        powershell_command="Get-Process | Where-Object {$_.Name -eq 'test_process'}",
        severity="INFO"
    )
    
    monitor._log_action(test_action)
    
    # Test 3: Check recent actions
    print("\n3. Checking recent actions...")
    recent_actions = monitor.get_recent_actions(10)
    print(f"   Found {len(recent_actions)} recent actions")
    
    for action in recent_actions[-5:]:  # Show last 5
        print(f"   - {action.timestamp}: {action.action_type} - {action.description}")
    
    # Test 4: Export report
    print("\n4. Testing report export...")
    report_file = monitor.export_actions_report("test_admin_report.json")
    if report_file:
        print(f"   Report exported to: {report_file}")
    else:
        print("   Failed to export report")
    
    # Stop monitoring
    print("\n5. Stopping monitoring...")
    monitor.stop_monitoring()
    
    print("\nTest completed successfully!")
    print(f"Total actions logged: {len(monitor.actions_log)}")
    
    return monitor

def demonstrate_powershell_commands():
    """Demonstrate equivalent PowerShell commands."""
    print("\n" + "=" * 60)
    print("EQUIVALENT POWERSHELL COMMANDS DEMONSTRATION")
    print("=" * 60)
    
    commands = {
        "Service Monitoring": [
            "Get-Service | Select-Object Name,Status,StartType",
            "Get-Service | Where-Object {$_.Status -eq 'Stopped'}",
            "Get-WinEvent -FilterHashtable @{LogName='System'; ID=7034,7035,7036; StartTime=(Get-Date).AddHours(-1)}"
        ],
        "User Account Monitoring": [
            "Get-LocalUser | Select-Object Name,Enabled,PasswordRequired",
            "Get-LocalUser | Where-Object {$_.Enabled -eq $false}",
            "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624; StartTime=(Get-Date).AddHours(-1)}"
        ],
        "Registry Monitoring": [
            "Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'",
            "Get-ItemProperty 'HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run'",
            "Get-ChildItem 'HKLM:\\SYSTEM\\CurrentControlSet\\Services' | Select-Object Name"
        ],
        "Security Policy Monitoring": [
            "secedit /export /cfg temp_policy.cfg && Get-Content temp_policy.cfg",
            "Get-ItemProperty 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Policies\\System'",
            "whoami /priv"
        ],
        "System Configuration": [
            "Get-ComputerInfo | Select-Object WindowsProductName,TotalPhysicalMemory,Domain",
            "Get-NetAdapter | Where-Object {$_.Status -eq 'Up'}",
            "Get-NetFirewallProfile | Select-Object Name,Enabled"
        ]
    }
    
    for category, cmd_list in commands.items():
        print(f"\n{category}:")
        for i, cmd in enumerate(cmd_list, 1):
            print(f"  {i}. {cmd}")
    
    print("\n" + "=" * 60)
    print("NOTE: Some commands require elevated privileges (Run as Administrator)")
    print("Security Event Log access typically requires elevation.")
    print("=" * 60)

def show_usage_examples():
    """Show usage examples for the monitoring system."""
    print("\n" + "=" * 60)
    print("USAGE EXAMPLES")
    print("=" * 60)
    
    examples = """
1. Basic Monitoring:
   python admin_actions_monitor.py
   
2. Import and use in your script:
   from admin_actions_monitor import AdminActionsMonitor
   monitor = AdminActionsMonitor()
   monitor.start_monitoring()
   
3. Run PowerShell equivalent:
   powershell -ExecutionPolicy Bypass -File Admin-Monitor-PowerShell.ps1
   
4. Check specific service:
   Get-Service -Name "Spooler" | Format-List *
   
5. Monitor registry changes:
   Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run"
   
6. Check user privileges:
   whoami /priv
   
7. Export security policies:
   secedit /export /cfg security_policy.cfg
   
8. Monitor firewall status:
   Get-NetFirewallProfile | Select-Object Name,Enabled
"""
    
    print(examples)

if __name__ == "__main__":
    try:
        # Run the test
        monitor = test_monitoring()
        
        # Show PowerShell equivalents
        demonstrate_powershell_commands()
        
        # Show usage examples
        show_usage_examples()
        
        print("\n" + "=" * 60)
        print("MONITORING FILES CREATED:")
        print("- admin_actions.log (Text log)")
        print("- admin_actions.json (JSON log)")
        print("- test_admin_report.json (Test report)")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during testing: {e}")
        sys.exit(1)
