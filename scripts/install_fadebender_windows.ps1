param(
  [string]$RepoDir = "$env:USERPROFILE\ai-projects\fadebender",
  [int]$Port = 8722,
  [switch]$OpenFirewall = $true
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Info($msg) { Write-Host "[fadebender] $msg" }
function Err($msg)  { Write-Host "[fadebender][error] $msg" -ForegroundColor Red }

$remoteSrc = Join-Path $RepoDir 'ableton_remote\Fadebender'
if (-not (Test-Path $remoteSrc)) { Err "Remote Script not found: $remoteSrc"; exit 1 }

$appDir  = Join-Path $env:USERPROFILE '.fadebender'
$rsBase  = Join-Path $env:USERPROFILE 'Documents\Ableton\User Library\Remote Scripts'

# Try to detect custom User Library from Ableton preferences
try {
  $pref = Get-ChildItem "$env:APPDATA\Ableton\Live *\Preferences\Preferences.cfg" -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($pref) {
    $content = Get-Content $pref.FullName -Raw
    if ($content -match 'User\s*Library.*?Value=\"([^\"]+)\"') {
      $userLib = $Matches[1]
      if (Test-Path $userLib) { $rsBase = Join-Path $userLib 'Remote Scripts' }
    }
  }
} catch {}

New-Item -ItemType Directory -Force -Path $appDir | Out-Null
New-Item -ItemType Directory -Force -Path $rsBase | Out-Null

$rsDst = Join-Path $rsBase 'Fadebender'
if (Test-Path $rsDst) { Remove-Item $rsDst -Recurse -Force }
Copy-Item $remoteSrc $rsDst -Recurse
Info "Installed Remote Script to $rsDst"

# Create run_server.ps1
$runScriptPath = Join-Path $appDir 'run_server.ps1'
$runScript = @"
Start-Transcript -Path "`$env:TEMP\fadebender.log" -Append | Out-Null
`$env:ENV = 'production'
Set-Location "$RepoDir"
# If using a venv: if (Test-Path .venv\Scripts\Activate.ps1) { . .venv\Scripts\Activate.ps1 }
python -m uvicorn server.app:app --host 0.0.0.0 --port $Port --workers 1
Stop-Transcript
"@
Set-Content -Path $runScriptPath -Value $runScript -Encoding UTF8
Info "Wrote $runScriptPath"

# Task Scheduler entry
$taskName = 'FadebenderAgent'
& schtasks /Query /TN $taskName /F *> $null
if ($LASTEXITCODE -eq 0) { & schtasks /Delete /TN $taskName /F | Out-Null }
& schtasks /Create /SC ONLOGON /RL LIMITED /TN $taskName /TR "powershell.exe -ExecutionPolicy Bypass -File `"$runScriptPath`"" | Out-Null
Info "Created Task Scheduler entry: $taskName"

# Optional firewall rule (admin)
if ($OpenFirewall) {
  try {
    Start-Process -Verb RunAs -FilePath powershell -ArgumentList "-NoProfile -WindowStyle Hidden -Command New-NetFirewallRule -DisplayName 'Fadebender API' -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow" -Wait | Out-Null
    Info "Opened firewall for TCP port $Port"
  } catch {
    Err "Failed to create firewall rule (you can add it manually later)."
  }
}

# Start now (non-blocking)
Start-Process powershell -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$runScriptPath`"" | Out-Null
Info "✅ Installed. Open http://<this-pc-ip>:$Port/health"

