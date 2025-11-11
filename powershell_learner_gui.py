#!/usr/bin/env python3
"""
PowerShell Learner GUI
Real-time display of Windows actions with equivalent PowerShell commands.

This GUI shows user actions in Windows and displays the corresponding PowerShell commands,
helping users learn PowerShell through practical examples.
"""

import sys
import threading
import queue
from datetime import datetime
from typing import Optional, Dict, Any

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, font
except ImportError:
    print("ERROR: tkinter not available!")
    print("Please install tkinter for your Python distribution.")
    sys.exit(1)


class PowerShellLearnerGUI:
    """
    GUI window for displaying real-time PowerShell command equivalents
    for Windows system actions.
    """

    def __init__(self, title="PowerShell Learner - Live Feed"):
        self.title = title
        self.root = None
        self.event_queue = queue.Queue()
        self.running = False

        # Color scheme for different event types
        self.colors = {
            'SERVICE': '#FF6B6B',      # Red
            'REGISTRY': '#4ECDC4',     # Cyan
            'USER': '#95E1D3',         # Light green
            'FILE': '#F38181',         # Light red
            'PROCESS': '#AA96DA',      # Purple
            'NETWORK': '#FCBAD3',      # Pink
            'POLICY': '#FFFFD2',       # Yellow
            'DEFAULT': '#E8E8E8'       # Light gray
        }

    def start(self):
        """Start the GUI in a separate thread"""
        self.running = True
        gui_thread = threading.Thread(target=self._run_gui, daemon=True)
        gui_thread.start()

    def _run_gui(self):
        """Run the main GUI loop"""
        self.root = tk.Tk()
        self.root.title(self.title)
        self.root.geometry("1000x700")
        self.root.configure(bg='#2C3E50')

        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        self._create_widgets()
        self._start_update_loop()

        self.root.mainloop()

    def _create_widgets(self):
        """Create all GUI widgets"""

        # Header
        header_frame = tk.Frame(self.root, bg='#34495E', height=60)
        header_frame.grid(row=0, column=0, sticky='ew', padx=0, pady=0)
        header_frame.grid_propagate(False)

        title_font = font.Font(family='Segoe UI', size=18, weight='bold')
        title_label = tk.Label(
            header_frame,
            text="🎓 PowerShell Learner - Live Command Feed",
            font=title_font,
            bg='#34495E',
            fg='#ECF0F1'
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=15)

        # Status indicator
        self.status_label = tk.Label(
            header_frame,
            text="● Monitoring",
            font=font.Font(family='Segoe UI', size=10),
            bg='#34495E',
            fg='#2ECC71'
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # Main content area with scrolled text
        content_frame = tk.Frame(self.root, bg='#2C3E50')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=10, pady=10)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=1)

        # Text widget for displaying events
        self.text_widget = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            font=font.Font(family='Consolas', size=10),
            bg='#1E272E',
            fg='#ECF0F1',
            insertbackground='#ECF0F1',
            padx=10,
            pady=10,
            relief=tk.FLAT
        )
        self.text_widget.grid(row=0, column=0, sticky='nsew')

        # Configure text tags for styling
        self._configure_text_tags()

        # Control buttons frame
        button_frame = tk.Frame(self.root, bg='#2C3E50', height=50)
        button_frame.grid(row=2, column=0, sticky='ew', padx=10, pady=(0, 10))

        button_style = {
            'font': font.Font(family='Segoe UI', size=10),
            'bg': '#3498DB',
            'fg': 'white',
            'relief': tk.FLAT,
            'padx': 20,
            'pady': 8,
            'cursor': 'hand2'
        }

        clear_btn = tk.Button(
            button_frame,
            text="🗑️ Clear Log",
            command=self._clear_log,
            **button_style
        )
        clear_btn.pack(side=tk.LEFT, padx=5)

        save_btn = tk.Button(
            button_frame,
            text="💾 Save to File",
            command=self._save_to_file,
            **button_style
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        # Event counter
        self.event_count_label = tk.Label(
            button_frame,
            text="Events: 0",
            font=font.Font(family='Segoe UI', size=10),
            bg='#2C3E50',
            fg='#ECF0F1'
        )
        self.event_count_label.pack(side=tk.RIGHT, padx=10)

        self.event_count = 0

    def _configure_text_tags(self):
        """Configure text tags for different styles"""
        # Timestamp tag
        self.text_widget.tag_config(
            'timestamp',
            foreground='#95A5A6',
            font=font.Font(family='Consolas', size=9)
        )

        # Event type tags
        self.text_widget.tag_config(
            'event_type',
            foreground='#3498DB',
            font=font.Font(family='Consolas', size=10, weight='bold')
        )

        # Description tag
        self.text_widget.tag_config(
            'description',
            foreground='#ECF0F1',
            font=font.Font(family='Consolas', size=10)
        )

        # PowerShell header
        self.text_widget.tag_config(
            'ps_header',
            foreground='#2ECC71',
            font=font.Font(family='Consolas', size=10, weight='bold')
        )

        # PowerShell command
        self.text_widget.tag_config(
            'ps_command',
            foreground='#F39C12',
            font=font.Font(family='Consolas', size=10, slant='italic'),
            background='#16202B'
        )

        # Separator
        self.text_widget.tag_config(
            'separator',
            foreground='#34495E'
        )

        # Event type specific colors
        for event_type, color in self.colors.items():
            self.text_widget.tag_config(f'color_{event_type}', foreground=color)

    def _start_update_loop(self):
        """Start the periodic update loop to check for new events"""
        self._update_from_queue()

    def _update_from_queue(self):
        """Check queue for new events and display them"""
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._display_event(event)
                self.event_count += 1
                self.event_count_label.config(text=f"Events: {self.event_count}")
        except queue.Empty:
            pass

        # Schedule next update
        if self.running:
            self.root.after(100, self._update_from_queue)

    def _display_event(self, event: Dict[str, Any]):
        """Display an event in the text widget"""
        self.text_widget.config(state=tk.NORMAL)

        # Determine event category for coloring
        event_type = event.get('type', 'DEFAULT')
        category = self._get_category(event_type)

        # Timestamp
        timestamp = event.get('timestamp', datetime.now().isoformat())
        self.text_widget.insert(tk.END, f"[{timestamp}] ", 'timestamp')

        # Event type
        self.text_widget.insert(tk.END, f"{event_type}", ('event_type', f'color_{category}'))
        self.text_widget.insert(tk.END, "\n")

        # Description
        description = event.get('description', 'No description')
        self.text_widget.insert(tk.END, f"  📋 {description}\n", 'description')

        # PowerShell command
        ps_command = event.get('powershell_command', '')
        if ps_command:
            self.text_widget.insert(tk.END, "  💻 PowerShell: ", 'ps_header')
            self.text_widget.insert(tk.END, f"{ps_command}\n", 'ps_command')

        # Additional details (optional)
        details = event.get('details', {})
        if details and isinstance(details, dict):
            for key, value in list(details.items())[:3]:  # Show max 3 details
                self.text_widget.insert(
                    tk.END,
                    f"     • {key}: {value}\n",
                    'description'
                )

        # Separator
        self.text_widget.insert(tk.END, "  " + "─" * 90 + "\n\n", 'separator')

        # Auto-scroll to bottom
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)

    def _get_category(self, event_type: str) -> str:
        """Determine the category of an event type for coloring"""
        event_type_upper = event_type.upper()

        if 'SERVICE' in event_type_upper:
            return 'SERVICE'
        elif 'REGISTRY' in event_type_upper:
            return 'REGISTRY'
        elif 'USER' in event_type_upper or 'ACCOUNT' in event_type_upper:
            return 'USER'
        elif 'FILE' in event_type_upper:
            return 'FILE'
        elif 'PROCESS' in event_type_upper:
            return 'PROCESS'
        elif 'NETWORK' in event_type_upper:
            return 'NETWORK'
        elif 'POLICY' in event_type_upper:
            return 'POLICY'
        else:
            return 'DEFAULT'

    def add_event(self, event_type: str, description: str, powershell_command: str,
                  details: Optional[Dict[str, Any]] = None, timestamp: Optional[str] = None):
        """
        Add an event to the display queue

        Args:
            event_type: Type of event (e.g., "SERVICE_STATUS_CHANGED")
            description: Human-readable description of the event
            powershell_command: Equivalent PowerShell command
            details: Optional dictionary with additional details
            timestamp: Optional ISO format timestamp
        """
        event = {
            'type': event_type,
            'description': description,
            'powershell_command': powershell_command,
            'details': details or {},
            'timestamp': timestamp or datetime.now().isoformat()
        }
        self.event_queue.put(event)

    def _clear_log(self):
        """Clear the log display"""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.config(state=tk.DISABLED)
        self.event_count = 0
        self.event_count_label.config(text="Events: 0")

    def _save_to_file(self):
        """Save the current log to a file"""
        try:
            filename = f"powershell_learner_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            content = self.text_widget.get('1.0', tk.END)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Log saved to: {filename}")
            # TODO: Show a success message in GUI
        except Exception as e:
            print(f"Error saving log: {e}")
            # TODO: Show error message in GUI

    def stop(self):
        """Stop the GUI"""
        self.running = False
        if self.root:
            self.root.quit()


def demo():
    """Demo function to test the GUI"""
    import time

    gui = PowerShellLearnerGUI()
    gui.start()

    # Wait for GUI to initialize
    time.sleep(1)

    # Add some demo events
    gui.add_event(
        "SERVICE_STATUS_CHANGED",
        "Service 'Spooler' changed from RUNNING to STOPPED",
        "Stop-Service -Name 'Spooler'",
        {"service_name": "Spooler", "old_status": "RUNNING", "new_status": "STOPPED"}
    )

    time.sleep(2)

    gui.add_event(
        "REGISTRY_VALUE_ADDED",
        "New startup program added to registry",
        "Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run' -Name 'MyApp' -Value 'C:\\MyApp.exe'",
        {"key": "Run", "value_name": "MyApp"}
    )

    time.sleep(2)

    gui.add_event(
        "USER_ACCOUNT_CHANGE",
        "User account 'TestUser' was disabled",
        "Disable-LocalUser -Name 'TestUser'",
        {"username": "TestUser", "change": "Account disabled"}
    )

    time.sleep(2)

    gui.add_event(
        "PROCESS_CREATED",
        "Process 'notepad.exe' was started",
        "Start-Process -FilePath 'notepad.exe'",
        {"pid": 1234, "exe": "C:\\Windows\\System32\\notepad.exe"}
    )

    time.sleep(2)

    gui.add_event(
        "FILE_CREATED",
        "File created: C:\\Users\\Public\\test.txt",
        "New-Item -Path 'C:\\Users\\Public\\test.txt' -ItemType File",
        {"path": "C:\\Users\\Public\\test.txt"}
    )

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        gui.stop()


if __name__ == "__main__":
    demo()
