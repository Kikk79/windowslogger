#!/usr/bin/env python3
"""
Example usage of the Windows System Monitor
Demonstrates basic setup and customization options
"""

import json
import time
import os
from windows_monitor import WindowsMonitor

def create_custom_config():
    """Create a custom monitoring configuration"""
    custom_config = {
        "monitoring": {
            "processes": True,
            "registry": True,
            "filesystem": True,
            "event_logs": True,
            "network": True
        },
        "paths_to_watch": [
            # Monitor specific directories for demonstration
            "C:\\Users\\Public",
            "C:\\Windows\\Temp",
            # Add your own paths here
        ],
        "registry_keys": [
            "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
            "HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run",
            # Add custom registry keys to monitor
        ],
        "event_logs": [
            "System",
            "Application",
            # Note: Security log requires admin privileges
        ],
        "output_file": "custom_monitor_events.json",
        "log_level": "INFO",
        "max_events": 500,
        "check_interval": 3  # Check every 3 seconds for more responsive monitoring
    }
    
    # Save custom configuration
    with open("custom_monitor_config.json", 'w') as f:
        json.dump(custom_config, f, indent=2)
    
    print("Custom configuration created: custom_monitor_config.json")
    return custom_config

def demo_basic_monitoring():
    """Demonstrate basic monitoring setup"""
    print("=== Basic Windows System Monitor Demo ===")
    print()
    
    # Create monitor with default configuration
    monitor = WindowsMonitor()
    
    try:
        print("Starting monitoring with default configuration...")
        print("Monitor will capture:")
        print("- Process creation/termination")
        print("- Registry changes")
        print("- File system events")
        print("- Windows Event Log entries")
        print("- Network connections")
        print()
        
        # Start monitoring
        monitor.start_monitoring()
        
        print("Monitoring active. Create some files, run programs, or modify registry to see events.")
        print("Press Ctrl+C to stop monitoring...")
        print()
        
        # Let it run for demonstration
        start_time = time.time()
        while time.time() - start_time < 60:  # Run for 1 minute
            time.sleep(1)
            # Print current event count
            if len(monitor.events) > 0:
                print(f"\rEvents captured: {len(monitor.events)}", end="")
        
        print(f"\nDemo completed. Total events captured: {len(monitor.events)}")
        
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    
    finally:
        monitor.stop_monitoring()
        print("Monitor stopped.")
        
        # Show sample events
        if monitor.events:
            print(f"\nSample events (showing last 3 of {len(monitor.events)}):")
            for event in monitor.events[-3:]:
                print(f"- {event['timestamp']}: {event['type']}")

def demo_custom_monitoring():
    """Demonstrate custom monitoring configuration"""
    print("=== Custom Configuration Demo ===")
    print()
    
    # Create custom configuration
    config = create_custom_config()
    
    # Create monitor with custom configuration
    monitor = WindowsMonitor("custom_monitor_config.json")
    
    try:
        print("Starting monitoring with custom configuration...")
        print(f"Check interval: {config['check_interval']} seconds")
        print(f"Max events: {config['max_events']}")
        print(f"Output file: {config['output_file']}")
        print()
        
        # Start monitoring
        monitor.start_monitoring()
        
        print("Custom monitoring active. Try creating files in monitored directories.")
        print("Press Ctrl+C to stop...")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nStopping custom monitor...")
    
    finally:
        monitor.stop_monitoring()
        print("Custom monitor stopped.")

def show_event_analysis():
    """Analyze captured events and show statistics"""
    print("=== Event Analysis ===")
    
    # Check if events file exists
    if not os.path.exists("monitor_events.json"):
        print("No events file found. Run monitoring first.")
        return
    
    # Load events
    with open("monitor_events.json", 'r') as f:
        events = json.load(f)
    
    if not events:
        print("No events captured yet.")
        return
    
    # Analyze event types
    event_types = {}
    for event in events:
        event_type = event['type']
        event_types[event_type] = event_types.get(event_type, 0) + 1
    
    print(f"Total events: {len(events)}")
    print("\nEvent breakdown:")
    for event_type, count in sorted(event_types.items()):
        print(f"  {event_type}: {count}")
    
    # Show recent events
    print(f"\nMost recent events (last 5):")
    for event in events[-5:]:
        timestamp = event['timestamp'].split('T')[1][:8]  # Extract time
        print(f"  {timestamp} - {event['type']}")

def main():
    """Main demonstration function"""
    print("Windows System Monitor - Example Usage")
    print("=" * 50)
    print()
    
    while True:
        print("Choose an option:")
        print("1. Run basic monitoring demo (1 minute)")
        print("2. Run custom configuration demo")
        print("3. Analyze captured events")
        print("4. Exit")
        print()
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == '1':
            demo_basic_monitoring()
        elif choice == '2':
            demo_custom_monitoring()
        elif choice == '3':
            show_event_analysis()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        print("\n" + "=" * 50 + "\n")

if __name__ == "__main__":
    main()
