# Mazzaroth Watchdog - Self-healing daemon for production resilience.
# Runs in background: checks mazz.py (watch daemon) and mazzaroth_web.py
# If either process is missing, force-restarts it.
# Logs heartbeats to Mazzaroth_Engine_Data/watchdog.log
#
# Usage (Admin PowerShell):
#   powershell -ExecutionPolicy Bypass -File watchdog.ps1
#
# To install as a scheduled task (auto-start on boot):
#   $action = New-ScheduledTaskAction -Execute "powershell.exe" `
#     -Argument "-ExecutionPolicy Bypass -File `"$PSScriptRoot\watchdog.ps1`""
#   $trigger = New-ScheduledTaskTrigger -AtStartup
#   Register-ScheduledTask -TaskName "MazzarothWatchdog" `
#     -Action $action -Trigger $trigger -RunLevel Highest

param(
    [int]$IntervalSeconds = 60,
    [string]$MazzPath = $PSScriptRoot
)

$logDir = Join-Path $MazzPath "Mazzaroth_Engine_Data"
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$logFile = Join-Path $logDir "watchdog.log"
$pidFile = Join-Path $logDir "watchdog.pid"

# Write our PID
[System.IO.File]::WriteAllText($pidFile, [string]$PID)

function Log {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "$ts | $Message"
    Add-Content -Path $logFile -Value $line
    Write-Host $line
}

function Ensure-Process {
    param(
        [string]$Name,
        [string]$Script,
        [string]$Args
    )
    $proc = Get-Process -Name $Name -ErrorAction SilentlyContinue
    if (-not $proc -or $proc.HasExited) {
        Log "MISSING: $Script - restarting..."
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "python"
        $psi.Arguments = "$Script $Args"
        $psi.WorkingDirectory = $MazzPath
        $psi.UseShellExecute = $true
        $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
        [System.Diagnostics.Process]::Start($psi) | Out-Null
        Log "RESTARTED: $Script"
    }
}

function Get-MemoryMB {
    param([string]$Name)
    $proc = Get-Process -Name $Name -ErrorAction SilentlyContinue
    if ($proc) { return [math]::Round($proc.WorkingSet64 / 1MB, 1) }
    return 0
}

Log "WATCHDOG STARTED (PID $PID) - checking every ${IntervalSeconds}s"

while ($true) {
    # Check watch daemon (python process running mazz.py watch)
    $watchProc = Get-Process -Name "python" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "mazz.py watch" -or $_.CommandLine -match "mazz\.py.*watch" } |
        Select-Object -First 1

    if (-not $watchProc) {
        Log "WATCH MISSING - restarting mazz.py watch daemon"
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "python"
        $psi.Arguments = "mazz.py watch"
        $psi.WorkingDirectory = $MazzPath
        $psi.UseShellExecute = $true
        $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
        [System.Diagnostics.Process]::Start($psi) | Out-Null
        Log "WATCH RESTARTED"
    }

    # Check web dashboard
    $webProc = Get-Process -Name "python" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "mazzaroth_web.py" } |
        Select-Object -First 1

    if (-not $webProc) {
        Log "DASHBOARD MISSING - restarting mazzaroth_web.py"
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = "python"
        $psi.Arguments = "mazzaroth_web.py"
        $psi.WorkingDirectory = $MazzPath
        $psi.UseShellExecute = $true
        $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
        [System.Diagnostics.Process]::Start($psi) | Out-Null
        Log "DASHBOARD RESTARTED"
    }

    # Memory check - kill and restart if leaking (>200MB per python process)
    $pyProcs = Get-Process -Name "python" -ErrorAction SilentlyContinue
    foreach ($p in $pyProcs) {
        $mb = [math]::Round($p.WorkingSet64 / 1MB, 1)
        if ($mb -gt 200) {
            Log "LEAK DETECTED: $($p.Id) using ${mb}MB - restarting"
            $p.Kill()
        }
    }

    # Health report
    $watchMB = Get-MemoryMB "python"
    $webMB = Get-MemoryMB "python"
    $dashboardOk = (Get-Process -Name "python" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "mazzaroth_web.py" }) -ne $null
    $watchOk = (Get-Process -Name "python" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match "mazz.py watch" }) -ne $null
    Log "HEARTBEAT: Watch=$watchOk Dashboard=$dashboardOk"

    Start-Sleep -Seconds $IntervalSeconds
}
