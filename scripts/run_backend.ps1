param(
    [string]$HostName = "0.0.0.0",
    [int]$Port = 8765,
    [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root ".venv310\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    py -3.10 -m venv (Join-Path $Root ".venv310")
}

if ($InstallDeps) {
    & $Python -m pip install --upgrade pip
    & $Python -m pip install -r (Join-Path $Root "backend\requirements.txt")
}

$env:DORMFLOW_HOST = $HostName
$env:DORMFLOW_PORT = "$Port"
& $Python (Join-Path $Root "main.py") backend
