#!/usr/bin/env python3
"""
Test script to verify that all required dependencies are properly installed
and that basic functionality works on the current Windows system.
"""

import sys
import os
import platform

def test_python_version():
    """Test Python version compatibility"""
    print("Testing Python version...")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major >= 3 and version.minor >= 7:
        print("✓ Python version is compatible")
        return True
    else:
        print("✗ Python version is too old. Requires Python 3.7+")
        return False

def test_operating_system():
    """Test operating system compatibility"""
    print("\nTesting operating system...")
    system = platform.system()
    print(f"Operating system: {system}")
    
    if system == "Windows":
        print("✓ Running on Windows")
        return True
    else:
        print("✗ This script is designed for Windows only")
        return False

def test_dependency_imports():
    """Test importing all required dependencies"""
    print("\nTesting dependency imports...")
    
    dependencies = [
        ("psutil", "System and process utilities"),
        ("watchdog", "File system event monitoring"),
        ("win32evtlog", "Windows Event Log access (pywin32)"),
        ("win32evtlogutil", "Windows Event Log utilities (pywin32)"),
        ("winreg", "Windows Registry access"),
        ("win32api", "Windows API access (pywin32)"),
        ("win32con", "Windows constants (pywin32)"),
        ("pywintypes", "Python Windows types (pywin32)")
    ]
    
    success_count = 0
    
    for module_name, description in dependencies:
        try:
            __import__(module_name)
            print(f"✓ {module_name}: {description}")
            success_count += 1
        except ImportError as e:
            print(f"✗ {module_name}: {description} - FAILED ({e})")
    
    print(f"\nDependency test results: {success_count}/{len(dependencies)} modules imported successfully")
    return success_count == len(dependencies)

def test_basic_functionality():
    """Test basic functionality of key components"""
    print("\nTesting basic functionality...")
    
    try:
        # Test psutil
        import psutil
        processes = list(psutil.process_iter(['pid', 'name']))
        print(f"✓ psutil: Found {len(processes)} running processes")
    except Exception as e:
        print(f"✗ psutil functionality test failed: {e}")
        return False
    
    try:
        # Test registry access
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE") as key:
            print("✓ winreg: Successfully accessed registry")
    except Exception as e:
        print(f"✗ winreg functionality test failed: {e}")
        return False
    
    try:
        # Test watchdog
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
        observer = Observer()
        print("✓ watchdog: File system monitoring components available")
    except Exception as e:
        print(f"✗ watchdog functionality test failed: {e}")
        return False
    
    try:
        # Test Windows Event Log access
        import win32evtlog
        handle = win32evtlog.OpenEventLog(None, "System")
        if handle:
            win32evtlog.CloseEventLog(handle)
            print("✓ win32evtlog: Successfully accessed Windows Event Log")
        else:
            print("✗ win32evtlog: Failed to access Windows Event Log")
            return False
    except Exception as e:
        print(f"✗ win32evtlog functionality test failed: {e}")
        return False
    
    return True

def test_permissions():
    """Test permission levels"""
    print("\nTesting permissions...")
    
    try:
        import win32api
        import win32security
        
        # Check if running as administrator
        try:
            is_admin = win32security.GetTokenInformation(
                win32security.GetCurrentProcessToken(),
                win32security.TokenElevation
            )[1]
            if is_admin:
                print("✓ Running with administrator privileges")
            else:
                print("⚠ Running without administrator privileges")
                print("  Some features (like Security event log) may not work")
        except:
            print("? Unable to determine administrator status")
        
        return True
        
    except Exception as e:
        print(f"✗ Permission test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Windows System Monitor - Dependency Test")
    print("=" * 50)
    
    tests = [
        ("Python Version", test_python_version),
        ("Operating System", test_operating_system),
        ("Dependencies", test_dependency_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Permissions", test_permissions)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("✓ All tests passed! The Windows System Monitor should work correctly.")
        print("\nYou can now run:")
        print("  python windows_monitor.py")
        print("  python example_usage.py")
    else:
        print("✗ Some tests failed. Please install missing dependencies:")
        print("  pip install -r requirements.txt")
        print("\nIf pywin32 installation fails, try:")
        print("  pip install --upgrade pywin32")
        print("  python -m pywin32_postinstall")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
