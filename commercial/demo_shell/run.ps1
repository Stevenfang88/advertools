# Start Chinese demo shell on 127.0.0.1:8765 (Windows / GM241)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
if (-not $env:DEMO_SHELL_PASSWORD) { $env:DEMO_SHELL_PASSWORD = 'demo2026' }
if (-not $env:DEMO_SHELL_HOST) { $env:DEMO_SHELL_HOST = '127.0.0.1' }
if (-not $env:DEMO_SHELL_PORT) { $env:DEMO_SHELL_PORT = '8765' }
$env:PYTHONPATH = $Root
Write-Host "Starting demo_shell → http://$($env:DEMO_SHELL_HOST):$($env:DEMO_SHELL_PORT)/"
Write-Host "Basic Auth: any user / password=`$DEMO_SHELL_PASSWORD"
python -m demo_shell
