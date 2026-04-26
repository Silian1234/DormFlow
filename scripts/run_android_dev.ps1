param(
    [string]$Serial = "emulator-5554",
    [string]$PackageName = "org.dormflow.dormflow",
    [string]$ApkPath = "",
    [int]$BackendPort = 8765,
    [string]$HeadmanCode = "HEADMAN-2026",
    [switch]$CleanData,
    [switch]$SkipInstall,
    [switch]$StopBackend
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root ".venv310\Scripts\python.exe"
$RunDir = Join-Path $Root "qa-results\android-dev"
$PidFile = Join-Path $RunDir "backend.pid"
$DbPath = Join-Path $RunDir "backend.sqlite3"
$BackendOut = Join-Path $RunDir "backend_stdout.log"
$BackendErr = Join-Path $RunDir "backend_stderr.log"

if (-not $ApkPath) {
    $ApkPath = Join-Path $Root "apps\android\bin\dormflow-1.0.0-arm64-v8a_armeabi-v7a-debug.apk"
}

function Stop-RecordedBackend {
    if (-not (Test-Path $PidFile)) {
        return
    }
    $RecordedPid = (Get-Content $PidFile | Select-Object -First 1).Trim()
    if ($RecordedPid) {
        Get-Process -Id ([int]$RecordedPid) -ErrorAction SilentlyContinue | Stop-Process -Force
    }
    Remove-Item -LiteralPath $PidFile -ErrorAction SilentlyContinue
}

function Test-DormFlowBackend {
    try {
        $Health = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2
        return ($Health.status -eq "ok" -and $Health.service -eq "dormflow")
    } catch {
        return $false
    }
}

if ($StopBackend) {
    Stop-RecordedBackend
    Write-Host "Backend stopped if it was started by this runner."
    exit 0
}

if (-not (Test-Path $Python)) {
    throw "Python venv not found: $Python"
}
if (-not (Test-Path $ApkPath)) {
    throw "APK not found: $ApkPath"
}

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

if (-not (Test-DormFlowBackend)) {
    Stop-RecordedBackend
    Remove-Item -LiteralPath $BackendOut,$BackendErr -ErrorAction SilentlyContinue
    $Backend = Start-Process `
        -FilePath $Python `
        -ArgumentList @(
            "main.py",
            "backend",
            "--host",
            "0.0.0.0",
            "--port",
            "$BackendPort",
            "--database",
            $DbPath,
            "--headman-code",
            $HeadmanCode
        ) `
        -WorkingDirectory $Root `
        -PassThru `
        -WindowStyle Hidden `
        -RedirectStandardOutput $BackendOut `
        -RedirectStandardError $BackendErr
    $Backend.Id | Out-File $PidFile -Encoding ascii

    $Ready = $false
    for ($i = 0; $i -lt 50; $i++) {
        Start-Sleep -Milliseconds 200
        if (Test-DormFlowBackend) {
            $Ready = $true
            break
        }
        if ($Backend.HasExited) {
            break
        }
    }
    if (-not $Ready) {
        Get-Content $BackendErr -ErrorAction SilentlyContinue
        throw "DormFlow backend did not start on port $BackendPort"
    }
}

$Devices = adb devices
if (-not ($Devices | Select-String -SimpleMatch "$Serial")) {
    throw "Android device/emulator is not connected: $Serial"
}

if (-not $SkipInstall) {
    adb -s $Serial install -r $ApkPath
}
if ($CleanData) {
    adb -s $Serial shell pm clear $PackageName
}

$Activity = (adb -s $Serial shell cmd package resolve-activity --brief $PackageName | Select-Object -Last 1).Trim()
if (-not $Activity) {
    throw "Unable to resolve Android activity for $PackageName"
}
adb -s $Serial shell am start -n $Activity

Write-Host "ANDROID_DEV_READY"
Write-Host "Backend: http://127.0.0.1:$BackendPort"
Write-Host "Android API URL: http://10.0.2.2:$BackendPort"
Write-Host "Backend logs: $BackendOut"
Write-Host "Stop backend: powershell -ExecutionPolicy Bypass -File .\scripts\run_android_dev.ps1 -StopBackend"
