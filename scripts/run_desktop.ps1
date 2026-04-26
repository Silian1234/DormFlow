param(
  [switch]$InstallDeps
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

if (-not (Test-Path ".venv310")) {
  py -3.10 -m venv .venv310
}

if ($InstallDeps) {
  .\.venv310\Scripts\python.exe -m pip install --upgrade pip
  .\.venv310\Scripts\python.exe -m pip install -r requirements.txt
}

.\.venv310\Scripts\python.exe .\main.py

