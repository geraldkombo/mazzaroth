# Quinarian Engine — Full Setup for Windows
# Run this as Administrator to install everything
# Usage: powershell -ExecutionPolicy Bypass -File setup_quinarian.ps1

$MazzPath = $PSScriptRoot
$LogDir = Join-Path $MazzPath "Mazzaroth_Engine_Data"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  QUINARIAN ENGINE - FULL SETUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Generate ICS Calendar
Write-Host "[1/5] Generating ICS Calendar..." -ForegroundColor Yellow
Push-Location $MazzPath
python quinarian_engine.py ics
Pop-Location
Write-Host ""

# Step 2: Create ICS Sync Folder
Write-Host "[2/5] Creating ICS sync folder..." -ForegroundColor Yellow
$SyncDir = Join-Path $env:USERPROFILE "QuinarianSync"
if (-not (Test-Path $SyncDir)) {
    New-Item -ItemType Directory -Path $SyncDir -Force | Out-Null
}
Copy-Item (Join-Path $MazzPath "quinarian_calendar.ics") (Join-Path $SyncDir "quinarian_calendar.ics") -Force
Write-Host "  ICS deployed to: $SyncDir" -ForegroundColor Green
Write-Host ""

# Step 3: Install Scheduled Task for Daemon
Write-Host "[3/5] Installing Scheduled Task (auto-start daemon)..." -ForegroundColor Yellow

# Remove existing task if present
$taskName = "QuinarianDaemon"
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

$action = New-ScheduledTaskAction -Execute "python" `
    -Argument "quinarian_engine.py daemon" `
    -WorkingDirectory $MazzPath

$trigger = @(
    New-ScheduledTaskTrigger -Once -At (Get-Date).ToString("HH:mm") -RepetitionInterval (New-TimeSpan -Minutes 10) -RepetitionDuration (New-TimeSpan -Days 365)
)

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force
Write-Host "  Scheduled task '$taskName' installed." -ForegroundColor Green
Write-Host ""

# Step 4: Add to Watchdog
Write-Host "[4/5] Adding quinarian checks to watchdog..." -ForegroundColor Yellow
$WatchdogPath = Join-Path $MazzPath "watchdog.ps1"
if (Test-Path $WatchdogPath) {
    $watchdogContent = Get-Content $WatchdogPath -Raw
    if ($watchdogContent -notmatch "quinarian") {
        $addon = @"

# === QUINARIAN ENGINE CHECK ===
`$quinProc = Get-Process -Name "python" -ErrorAction SilentlyContinue |
    Where-Object { `$_.CommandLine -match "quinarian_engine.py daemon" } |
    Select-Object -First 1
if (-not `$quinProc) {
    Log "QUINARIAN DAEMON MISSING - restarting"
    `$psi = New-Object System.Diagnostics.ProcessStartInfo
    `$psi.FileName = "python"
    `$psi.Arguments = "quinarian_engine.py daemon"
    `$psi.WorkingDirectory = "`$MazzPath"
    `$psi.UseShellExecute = `$true
    `$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
    [System.Diagnostics.Process]::Start(`$psi) | Out-Null
    Log "QUINARIAN DAEMON RESTARTED"
}
"@
        Add-Content -Path $WatchdogPath -Value $addon
        Write-Host "  Watchdog updated with quinarian checks." -ForegroundColor Green
    } else {
        Write-Host "  Watchdog already has quinarian checks." -ForegroundColor Gray
    }
}
Write-Host ""

# Step 5: Test
Write-Host "[5/5] Testing..." -ForegroundColor Yellow
Push-Location $MazzPath
python quinarian_engine.py now
Pop-Location

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  SETUP COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  CALENDAR SYNC INSTRUCTIONS:" -ForegroundColor White
Write-Host "  ---------------------------"
Write-Host "  1. Open https://calendar.google.com"
Write-Host "  2. Settings -> Import & Export -> Import"
Write-Host "  3. Select: $SyncDir\quinarian_calendar.ics"
Write-Host "  4. Smart Watch: sync via Google Calendar app"
Write-Host ""
Write-Host "  COMMANDS:" -ForegroundColor White
Write-Host "  --------"
Write-Host "  python quinarian_engine.py now       # Current quinary"
Write-Host "  python quinarian_engine.py daemon    # Run daemon manually"
Write-Host "  python quinarian_engine.py ics       # Regenerate calendar"
Write-Host "  python quinarian_engine.py deploy FOLDER  # Deploy ICS"
Write-Host ""
Write-Host "  READING:" -ForegroundColor White
Write-Host "  - gerald_quinarian_reading.md"
Write-Host "  - dad_quinarian_reading.md"
Write-Host ""
