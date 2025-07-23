# Administrative Actions Monitoring - PowerShell Equivalent Commands
# This script demonstrates PowerShell commands equivalent to the Python pywin32 monitoring

# Set up logging
$LogFile = "admin_actions_powershell.log"
$JsonLog = "admin_actions_powershell.json"

function Write-AdminLog {
    param(
        [string]$Action,
        [string]$Description,
        [string]$Severity = "INFO",
        [hashtable]$Details = @{},
        [string]$PowerShellCommand = ""
    )
    
    $LogEntry = @{
        Timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
        ActionType = $Action
        Description = $Description
        User = $env:USERNAME
        Process = "PowerShell"
        Details = $Details
        PowerShellCommand = $PowerShellCommand
        Severity = $Severity
    }
    
    # Log to console and file
    $LogMessage = "$($LogEntry.Timestamp) - $($LogEntry.ActionType) - $Description"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
    
    # Save to JSON
    $LogEntry | ConvertTo-Json -Compress | Add-Content -Path $JsonLog
}

function Monitor-ServiceChanges {
    Write-Host "=== Monitoring Windows Services ===" -ForegroundColor Cyan
    
    # Get all services with detailed information
    $Services = Get-Service | Select-Object Name, Status, StartType, ServiceType
    
    Write-AdminLog -Action "SERVICE_ENUMERATION" -Description "Enumerating all Windows services" `
        -Details @{ ServiceCount = $Services.Count } `
        -PowerShellCommand "Get-Service | Select-Object Name,Status,StartType,ServiceType"
    
    # Monitor specific critical services
    $CriticalServices = @("Winlogon", "CSRSS", "Wininit", "Services", "Lsass", "Spooler", "Themes")
    
    foreach ($ServiceName in $CriticalServices) {
        try {
            $Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
            if ($Service) {
                Write-AdminLog -Action "CRITICAL_SERVICE_CHECK" `
                    -Description "Critical service '$ServiceName' status: $($Service.Status)" `
                    -Details @{ 
                        ServiceName = $ServiceName
                        Status = $Service.Status.ToString()
                        StartType = $Service.StartType.ToString()
                    } `
                    -PowerShellCommand "Get-Service -Name '$ServiceName' | Format-List *" `
                    -Severity "WARNING"
            }
        }
        catch {
            Write-AdminLog -Action "SERVICE_ERROR" `
                -Description "Could not query service: $ServiceName" `
                -Severity "ERROR"
        }
    }
    
    # Check for recently stopped/started services using Event Log
    Write-Host "Checking service events from Event Log..." -ForegroundColor Yellow
    try {
        $ServiceEvents = Get-WinEvent -FilterHashtable @{LogName='System'; ID=7034,7035,7036; StartTime=(Get-Date).AddHours(-1)} -MaxEvents 10 -ErrorAction SilentlyContinue
        
        foreach ($Event in $ServiceEvents) {
            $EventMessage = $Event.Message -replace "`n", " " -replace "`r", ""
            Write-AdminLog -Action "SERVICE_EVENT" `
                -Description "Service event detected: $($Event.Id)" `
                -Details @{
                    EventId = $Event.Id
                    TimeCreated = $Event.TimeCreated
                    Message = $EventMessage.Substring(0, [Math]::Min(200, $EventMessage.Length))
                } `
                -PowerShellCommand "Get-WinEvent -FilterHashtable @{LogName='System'; ID=$($Event.Id); StartTime=(Get-Date).AddHours(-1)}" `
                -Severity "INFO"
        }
    }
    catch {
        Write-Host "Could not access Event Log for service events: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Monitor-UserAccounts {
    Write-Host "=== Monitoring User Accounts ===" -ForegroundColor Cyan
    
    # Get local users
    try {
        $LocalUsers = Get-LocalUser
        
        Write-AdminLog -Action "USER_ENUMERATION" -Description "Enumerating local user accounts" `
            -Details @{ UserCount = $LocalUsers.Count } `
            -PowerShellCommand "Get-LocalUser | Select-Object Name,Enabled,PasswordRequired,UserMayChangePassword"
        
        foreach ($User in $LocalUsers) {
            $UserDetails = @{
                Name = $User.Name
                Enabled = $User.Enabled
                PasswordRequired = $User.PasswordRequired
                UserMayChangePassword = $User.UserMayChangePassword
                PasswordExpires = $User.PasswordExpires
                LastLogon = $User.LastLogon
                AccountExpires = $User.AccountExpires
            }
            
            $Severity = if ($User.Enabled -and -not $User.PasswordRequired) { "HIGH" } else { "INFO" }
            
            Write-AdminLog -Action "USER_ACCOUNT_CHECK" `
                -Description "User account status: $($User.Name) - Enabled: $($User.Enabled)" `
                -Details $UserDetails `
                -PowerShellCommand "Get-LocalUser -Name '$($User.Name)' | Format-List *" `
                -Severity $Severity
        }
    }
    catch {
        Write-Host "Error checking local users: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check for recent logon events
    Write-Host "Checking recent logon events..." -ForegroundColor Yellow
    try {
        $LogonEvents = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624; StartTime=(Get-Date).AddHours(-1)} -MaxEvents 5 -ErrorAction SilentlyContinue
        
        foreach ($Event in $LogonEvents) {
            Write-AdminLog -Action "USER_LOGON_EVENT" `
                -Description "User logon detected" `
                -Details @{
                    EventId = $Event.Id
                    TimeCreated = $Event.TimeCreated
                    UserId = $Event.UserId
                } `
                -PowerShellCommand "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=4624; StartTime=(Get-Date).AddHours(-1)}" `
                -Severity "INFO"
        }
    }
    catch {
        Write-Host "Could not access Security Event Log (may require elevation): $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Monitor-SecurityPolicies {
    Write-Host "=== Monitoring Security Policies ===" -ForegroundColor Cyan
    
    # Check account policies using secedit
    try {
        $TempFile = [System.IO.Path]::GetTempFileName()
        $null = secedit /export /cfg $TempFile /quiet
        
        if (Test-Path $TempFile) {
            $PolicyContent = Get-Content $TempFile
            $AccountPolicies = $PolicyContent | Where-Object { $_ -match "^(MinimumPasswordAge|MaximumPasswordAge|MinimumPasswordLength|PasswordComplexity|PasswordHistorySize|LockoutBadCount)" }
            
            foreach ($Policy in $AccountPolicies) {
                if ($Policy -match "^(.+?)\s*=\s*(.+)$") {
                    Write-AdminLog -Action "SECURITY_POLICY_CHECK" `
                        -Description "Security policy: $($matches[1]) = $($matches[2])" `
                        -Details @{
                            PolicyName = $matches[1]
                            PolicyValue = $matches[2]
                        } `
                        -PowerShellCommand "secedit /export /cfg temp.cfg && Get-Content temp.cfg | Where-Object { `$_ -match '$($matches[1])' }" `
                        -Severity "INFO"
                }
            }
            
            Remove-Item $TempFile -Force -ErrorAction SilentlyContinue
        }
    }
    catch {
        Write-Host "Error checking security policies: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check UAC settings
    try {
        $UACSettings = @{
            EnableLUA = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "EnableLUA" -ErrorAction SilentlyContinue).EnableLUA
            ConsentPromptBehaviorAdmin = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "ConsentPromptBehaviorAdmin" -ErrorAction SilentlyContinue).ConsentPromptBehaviorAdmin
            PromptOnSecureDesktop = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name "PromptOnSecureDesktop" -ErrorAction SilentlyContinue).PromptOnSecureDesktop
        }
        
        Write-AdminLog -Action "UAC_POLICY_CHECK" `
            -Description "User Account Control settings checked" `
            -Details $UACSettings `
            -PowerShellCommand "Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System' | Select-Object EnableLUA,ConsentPromptBehaviorAdmin,PromptOnSecureDesktop" `
            -Severity "INFO"
    }
    catch {
        Write-Host "Error checking UAC settings: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Monitor-RegistryChanges {
    Write-Host "=== Monitoring Critical Registry Keys ===" -ForegroundColor Cyan
    
    # Critical registry locations to monitor
    $CriticalKeys = @(
        @{Path="HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; Name="HKLM Run Keys"},
        @{Path="HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"; Name="HKCU Run Keys"},
        @{Path="HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"; Name="HKLM RunOnce Keys"},
        @{Path="HKLM:\SYSTEM\CurrentControlSet\Services"; Name="System Services"},
        @{Path="HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"; Name="Winlogon Settings"}
    )
    
    foreach ($Key in $CriticalKeys) {
        try {
            if (Test-Path $Key.Path) {
                $RegItems = Get-ItemProperty $Key.Path -ErrorAction SilentlyContinue
                $ItemCount = ($RegItems | Get-Member -MemberType NoteProperty | Where-Object { $_.Name -notmatch "^PS" }).Count
                
                Write-AdminLog -Action "REGISTRY_CHECK" `
                    -Description "Registry key monitored: $($Key.Name)" `
                    -Details @{
                        RegistryPath = $Key.Path
                        ItemCount = $ItemCount
                        KeyName = $Key.Name
                    } `
                    -PowerShellCommand "Get-ItemProperty '$($Key.Path)' | Format-List" `
                    -Severity "INFO"
                
                # Check specific suspicious entries in Run keys
                if ($Key.Path -like "*Run*") {
                    $SuspiciousPatterns = @("temp", "tmp", "users", "appdata", "programdata")
                    $RegItems.PSObject.Properties | ForEach-Object {
                        if ($_.Name -notmatch "^PS" -and $_.Value) {
                            foreach ($Pattern in $SuspiciousPatterns) {
                                if ($_.Value -like "*$Pattern*") {
                                    Write-AdminLog -Action "SUSPICIOUS_REGISTRY_ENTRY" `
                                        -Description "Potentially suspicious registry entry: $($_.Name)" `
                                        -Details @{
                                            EntryName = $_.Name
                                            EntryValue = $_.Value
                                            RegistryPath = $Key.Path
                                            SuspiciousPattern = $Pattern
                                        } `
                                        -PowerShellCommand "Get-ItemProperty '$($Key.Path)' -Name '$($_.Name)'" `
                                        -Severity "HIGH"
                                }
                            }
                        }
                    }
                }
            }
        }
        catch {
            Write-Host "Error accessing registry key $($Key.Path): $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

function Monitor-SystemConfiguration {
    Write-Host "=== Monitoring System Configuration ===" -ForegroundColor Cyan
    
    # Get computer system information
    try {
        $ComputerInfo = Get-ComputerInfo | Select-Object WindowsProductName, TotalPhysicalMemory, CsProcessors, CsDomain, CsWorkgroup, CsName
        
        Write-AdminLog -Action "SYSTEM_CONFIG_CHECK" `
            -Description "System configuration checked" `
            -Details @{
                ProductName = $ComputerInfo.WindowsProductName
                TotalMemory = $ComputerInfo.TotalPhysicalMemory
                ProcessorCount = $ComputerInfo.CsProcessors.Count
                Domain = $ComputerInfo.CsDomain
                Workgroup = $ComputerInfo.CsWorkgroup
                ComputerName = $ComputerInfo.CsName
            } `
            -PowerShellCommand "Get-ComputerInfo | Select-Object WindowsProductName,TotalPhysicalMemory,CsProcessors,CsDomain,CsWorkgroup" `
            -Severity "INFO"
    }
    catch {
        Write-Host "Error getting computer information: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check network configuration
    try {
        $NetworkAdapters = Get-NetAdapter | Where-Object { $_.Status -eq "Up" } | Select-Object Name, InterfaceDescription, LinkSpeed
        
        Write-AdminLog -Action "NETWORK_CONFIG_CHECK" `
            -Description "Network configuration checked" `
            -Details @{
                ActiveAdapters = $NetworkAdapters.Count
                AdapterNames = $NetworkAdapters.Name
            } `
            -PowerShellCommand "Get-NetAdapter | Where-Object { `$_.Status -eq 'Up' } | Select-Object Name,InterfaceDescription,LinkSpeed" `
            -Severity "INFO"
    }
    catch {
        Write-Host "Error checking network configuration: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check firewall status
    try {
        $FirewallProfiles = Get-NetFirewallProfile | Select-Object Name, Enabled
        
        foreach ($Profile in $FirewallProfiles) {
            $Severity = if ($Profile.Enabled -eq $false) { "HIGH" } else { "INFO" }
            
            Write-AdminLog -Action "FIREWALL_STATUS_CHECK" `
                -Description "Firewall profile '$($Profile.Name)' is $($Profile.Enabled)" `
                -Details @{
                    ProfileName = $Profile.Name
                    Enabled = $Profile.Enabled
                } `
                -PowerShellCommand "Get-NetFirewallProfile -Name '$($Profile.Name)' | Select-Object Name,Enabled" `
                -Severity $Severity
        }
    }
    catch {
        Write-Host "Error checking firewall status: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Monitor-SecurityEvents {
    Write-Host "=== Monitoring Security Events ===" -ForegroundColor Cyan
    
    # Check current user privileges
    try {
        $CurrentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent()
        $Principal = New-Object System.Security.Principal.WindowsPrincipal($CurrentUser)
        
        $IsAdmin = $Principal.IsInRole([System.Security.Principal.WindowsBuiltInRole]::Administrator)
        $IsElevated = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
        
        Write-AdminLog -Action "PRIVILEGE_CHECK" `
            -Description "Current user privilege check" `
            -Details @{
                UserName = $CurrentUser.Name
                IsAdministrator = $IsAdmin
                IsElevated = $IsElevated
                AuthenticationType = $CurrentUser.AuthenticationType
            } `
            -PowerShellCommand "whoami /priv" `
            -Severity "INFO"
    }
    catch {
        Write-Host "Error checking user privileges: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    # Check for recent security events (if accessible)
    $SecurityEventIDs = @{
        4624 = "Successful Logon"
        4625 = "Failed Logon"
        4648 = "Logon with Explicit Credentials"
        4672 = "Special Privileges Assigned"
        4720 = "User Account Created"
        4722 = "User Account Enabled"
        4724 = "Password Reset"
        4732 = "Member Added to Security Group"
    }
    
    foreach ($EventID in $SecurityEventIDs.Keys) {
        try {
            $Events = Get-WinEvent -FilterHashtable @{LogName='Security'; ID=$EventID; StartTime=(Get-Date).AddHours(-1)} -MaxEvents 3 -ErrorAction SilentlyContinue
            
            foreach ($Event in $Events) {
                Write-AdminLog -Action "SECURITY_EVENT" `
                    -Description "Security event: $($SecurityEventIDs[$EventID])" `
                    -Details @{
                        EventId = $Event.Id
                        TimeCreated = $Event.TimeCreated
                        EventDescription = $SecurityEventIDs[$EventID]
                        MachineName = $Event.MachineName
                    } `
                    -PowerShellCommand "Get-WinEvent -FilterHashtable @{LogName='Security'; ID=$EventID; StartTime=(Get-Date).AddHours(-1)}" `
                    -Severity "WARNING"
            }
        }
        catch {
            # Security log access requires elevation, so this is expected to fail for normal users
            Write-Host "Could not access Security Event $EventID (requires elevation): $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

function Start-AdminMonitoring {
    Write-Host "Starting Administrative Actions Monitoring..." -ForegroundColor Green
    Write-Host "Log files: $LogFile and $JsonLog" -ForegroundColor Green
    Write-Host "=" * 60 -ForegroundColor Green
    
    # Initialize log files
    "Administrative Actions Monitoring Started - $(Get-Date)" | Out-File -FilePath $LogFile -Encoding UTF8
    
    try {
        Monitor-ServiceChanges
        Write-Host ""
        
        Monitor-UserAccounts  
        Write-Host ""
        
        Monitor-SecurityPolicies
        Write-Host ""
        
        Monitor-RegistryChanges
        Write-Host ""
        
        Monitor-SystemConfiguration
        Write-Host ""
        
        Monitor-SecurityEvents
        Write-Host ""
        
        Write-Host "Monitoring cycle completed successfully!" -ForegroundColor Green
        Write-Host "Check log files for detailed information:" -ForegroundColor Green
        Write-Host "  Text Log: $LogFile" -ForegroundColor Cyan
        Write-Host "  JSON Log: $JsonLog" -ForegroundColor Cyan
        
    }
    catch {
        Write-Host "Error during monitoring: $($_.Exception.Message)" -ForegroundColor Red
        Write-AdminLog -Action "MONITORING_ERROR" `
            -Description "Error occurred during monitoring cycle" `
            -Details @{
                ErrorMessage = $_.Exception.Message
                ErrorType = $_.Exception.GetType().Name
            } `
            -Severity "ERROR"
    }
}

# Main execution
if ($MyInvocation.InvocationName -eq $MyInvocation.MyCommand.Name) {
    Start-AdminMonitoring
}
