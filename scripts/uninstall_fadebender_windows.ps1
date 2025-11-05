Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Info($msg) { Write-Host "[fadebender] $msg" }

$taskName = 'FadebenderAgent'
& schtasks /Delete /TN $taskName /F *> $null
Info "Removed Task Scheduler entry (if existed): $taskName"

$runScriptPath = Join-Path $env:USERPROFILE '.fadebender\run_server.ps1'
if (Test-Path $runScriptPath) { Remove-Item $runScriptPath -Force }
Info "Removed run_server.ps1 (if existed)"

$rsDst = Join-Path $env:USERPROFILE 'Documents\Ableton\User Library\Remote Scripts\Fadebender'
if (Test-Path $rsDst) { Remove-Item $rsDst -Recurse -Force }
Info "Removed Remote Script from User Library (if existed)"

# Optional: remove firewall rule (if named exactly)
try { Remove-NetFirewallRule -DisplayName 'Fadebender API' } catch {}
Info "Cleanup complete."

