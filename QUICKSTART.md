# PowerShell Learner - Schnellstart-Anleitung

## Was ist PowerShell Learner?

**PowerShell Learner** ist ein Lern-Tool, das Ihre Windows-GUI-Aktionen in Echtzeit überwacht und die **äquivalenten PowerShell-Befehle** anzeigt.

**Ziel**: PowerShell durch praktische Beispiele lernen - nutzen Sie Windows wie gewohnt, und sehen Sie, wie man dieselben Aktionen mit PowerShell durchführt!

---

## Funktionsweise

```
Sie klicken in Windows:
  "Dienste" → Rechtsklick "Druckwarteschlange" → "Beenden"
         ↓
Tool erkennt und zeigt:
  PowerShell: Stop-Service -Name 'Spooler'
```

---

## Installation

### 1. Voraussetzungen

- **Windows 10/11** (funktioniert NICHT auf Linux/macOS)
- **Python 3.7+**
- **Administrator-Rechte** (empfohlen für volle Funktionalität)

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

Falls `pywin32` Probleme macht:

```bash
pip install --upgrade pywin32
python -m pywin32_postinstall
```

### 3. Dependencies testen

```bash
python test_dependencies.py
```

---

## Nutzung

### Hauptprogramm starten

```bash
python powershell_learner.py
```

Das Programm startet:
1. Ein **GUI-Fenster** mit Live-Feed der PowerShell-Befehle
2. **Hintergrund-Monitoring** Ihrer Windows-Aktionen

### Was wird überwacht?

✅ **Services** - Dienste starten/stoppen
✅ **Registry** - Registry-Einträge ändern
✅ **Dateisystem** - Dateien erstellen/löschen/verschieben
✅ **Prozesse** - Programme starten/beenden
✅ **Netzwerk** - Netzwerkverbindungen
✅ **Benutzer** - Benutzerkonten verwalten
✅ **Firewall** - Firewall-Regeln ändern
✅ **Scheduled Tasks** - Geplante Aufgaben
✅ **Environment Variables** - Umgebungsvariablen
✅ **Windows Features** - Optionale Features
✅ **Drucker** - Druckerkonfiguration

---

## Beispiel-Szenarien

### Szenario 1: Dienst stoppen

**Ihre Aktion:**
1. Öffnen Sie `services.msc`
2. Rechtsklick auf "Druckwarteschlange" (Spooler)
3. Klicken Sie "Beenden"

**PowerShell Learner zeigt:**
```powershell
Stop-Service -Name 'Spooler'
```

### Szenario 2: Startup-Programm hinzufügen

**Ihre Aktion:**
1. Öffnen Sie `regedit`
2. Navigieren zu `HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`
3. Erstellen Sie einen neuen String-Wert

**PowerShell Learner zeigt:**
```powershell
Set-ItemProperty -Path 'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run' -Name 'MyApp' -Value 'C:\MyApp.exe'
```

### Szenario 3: Datei erstellen

**Ihre Aktion:**
1. Öffnen Sie Windows Explorer
2. Erstellen Sie eine neue Textdatei in `C:\Temp`

**PowerShell Learner zeigt:**
```powershell
New-Item -Path 'C:\Temp\NewFile.txt' -ItemType File
```

---

## GUI-Features

### Live-Feed-Fenster

Das GUI zeigt in Echtzeit:
- **Zeitstempel** der Aktion
- **Event-Typ** (farbcodiert)
- **Beschreibung** der Aktion
- **PowerShell-Befehl** (hervorgehoben)
- **Details** (optional)

### Farbcodierung

- 🔴 **Rot** - Services
- 🔵 **Cyan** - Registry
- 🟢 **Grün** - Benutzer
- 🟣 **Lila** - Prozesse
- 🟡 **Gelb** - Richtlinien
- 🟠 **Orange** - Dateien

### Steuerelemente

- **🗑️ Clear Log** - Protokoll löschen
- **💾 Save to File** - Protokoll speichern
- **Event Counter** - Anzahl der erfassten Ereignisse

---

## Andere Programme

### Nur Monitoring (ohne GUI)

```bash
python windows_monitor.py
```

Überwacht das System und speichert Events in `monitor_events.json`.

### Admin-Actions Monitor

```bash
python admin_actions_monitor.py
```

Fokus auf administrative Aktionen mit PowerShell-Befehlen.

### Demo GUI testen

```bash
python powershell_learner_gui.py
```

Zeigt Demo-Events im GUI.

---

## Konfiguration

### Config-Datei: `monitor_config.json`

```json
{
  "monitoring": {
    "processes": true,
    "registry": true,
    "filesystem": true,
    "event_logs": true,
    "network": true,
    "services": true
  },
  "paths_to_watch": [
    "C:\\Users\\Public",
    "C:\\Windows\\Temp"
  ],
  "check_interval": 5,
  "max_events": 1000
}
```

**Wichtige Optionen:**
- `check_interval` - Polling-Intervall in Sekunden (Standard: 5)
- `paths_to_watch` - Dateipfade zum Überwachen
- `max_events` - Maximale Anzahl gecachter Events

---

## Tipps & Tricks

### 1. Als Administrator ausführen

Für volle Funktionalität (besonders Event Logs) als Admin starten:

```bash
# PowerShell als Admin
python powershell_learner.py
```

### 2. Performance-Optimierung

Für bessere Performance:
- Erhöhen Sie `check_interval` auf 10-15 Sekunden
- Reduzieren Sie `paths_to_watch` auf spezifische Verzeichnisse
- Deaktivieren Sie nicht benötigte Monitore

### 3. Lernmodus

**Empfohlener Workflow:**
1. Starten Sie PowerShell Learner
2. Führen Sie eine Aktion in Windows GUI aus
3. Notieren Sie den angezeigten PowerShell-Befehl
4. Testen Sie den Befehl in PowerShell
5. Wiederholen Sie für verschiedene Aktionen

---

## Fehlerbehebung

### "Error importing Windows libraries"

**Lösung:**
```bash
pip install --upgrade pywin32
python -m pywin32_postinstall
```

### "This tool only works on Windows"

**Problem:** Sie versuchen, das Tool auf Linux/macOS auszuführen.

**Lösung:** Nur auf Windows-Systemen nutzbar.

### GUI startet nicht

**Lösung:**
```bash
# Prüfen Sie ob tkinter installiert ist
python -c "import tkinter"
```

### Keine Events werden angezeigt

**Mögliche Ursachen:**
1. Keine Windows-Aktionen durchgeführt
2. Zu kurzes Polling-Intervall
3. Keine Admin-Rechte (für manche Events erforderlich)

---

## Erweiterte Nutzung

### Eigene Event-Handler hinzufügen

Bearbeiten Sie `powershell_learner.py` und erweitern Sie `PowerShellCommandGenerator.generate_command()`:

```python
elif event_type == "MY_CUSTOM_EVENT":
    return "My-PowerShellCommand -Parameter 'Value'"
```

### Eigene Monitore erstellen

Siehe `extended_monitors.py` als Beispiel:

```python
class MyCustomMonitor:
    def __init__(self, main_monitor):
        self.main_monitor = main_monitor

    def monitor(self):
        while self.main_monitor.running:
            # Monitoring-Logik
            self.main_monitor.log_event('CUSTOM_EVENT', data)
            time.sleep(10)
```

---

## Ausgabedateien

- `monitor_events.json` - Alle erfassten Events
- `windows_monitor.log` - Monitoring-Protokoll
- `admin_actions.json` - Administrative Aktionen
- `powershell_learner_log_*.txt` - Gespeicherte GUI-Logs

---

## Häufige PowerShell-Befehle

### Services
```powershell
Get-Service                           # Alle Dienste auflisten
Start-Service -Name 'ServiceName'    # Dienst starten
Stop-Service -Name 'ServiceName'     # Dienst stoppen
Restart-Service -Name 'ServiceName'  # Dienst neustarten
```

### Registry
```powershell
Get-ItemProperty -Path 'HKLM:\...'                    # Wert lesen
Set-ItemProperty -Path 'HKLM:\...' -Name 'X' -Value 'Y'  # Wert setzen
Remove-ItemProperty -Path 'HKLM:\...' -Name 'X'       # Wert löschen
```

### Dateien
```powershell
New-Item -Path 'C:\file.txt' -ItemType File  # Datei erstellen
Remove-Item -Path 'C:\file.txt'              # Datei löschen
Move-Item -Path 'C:\src' -Destination 'C:\dst'  # Datei verschieben
Copy-Item -Path 'C:\src' -Destination 'C:\dst'  # Datei kopieren
```

### Prozesse
```powershell
Get-Process                    # Alle Prozesse
Start-Process -FilePath 'app.exe'  # Prozess starten
Stop-Process -Name 'app'       # Prozess beenden (Name)
Stop-Process -Id 1234          # Prozess beenden (PID)
```

---

## Support

Bei Problemen oder Fragen:

1. Prüfen Sie `windows_monitor.log` für Fehler
2. Testen Sie mit `test_dependencies.py`
3. Stellen Sie sicher, dass Sie Windows verwenden
4. Führen Sie als Administrator aus

---

## Weitere Ressourcen

- **PowerShell Dokumentation**: https://docs.microsoft.com/powershell/
- **Windows API**: https://docs.microsoft.com/windows/win32/
- **pywin32 Dokumentation**: https://github.com/mhammond/pywin32

---

**Viel Erfolg beim PowerShell Lernen! 🎓**
