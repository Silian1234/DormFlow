param(
    [string]$Serial = "",
    [string]$PackageName = "org.dormflow.dormflow",
    [string]$ApkPath = "",
    [int]$BackendPort = 8765,
    [string]$HeadmanCode = "HEADMAN-2026",
    [switch]$UseAdbReverse,
    [switch]$CleanData,
    [switch]$SkipInstall,
    [switch]$StopBackend
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root ".venv310\Scripts\python.exe"
$RunDir = Join-Path $Root "qa-results\physical-android-dev"
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

function Get-LanIp {
    $Candidates = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object {
            $_.IPAddress -notlike "127.*" -and
            $_.IPAddress -notlike "169.254.*" -and
            $_.InterfaceAlias -notlike "*WSL*" -and
            $_.InterfaceAlias -notlike "*vEthernet*" -and
            $_.InterfaceAlias -notlike "*tun*" -and
            $_.InterfaceAlias -notlike "*VPN*"
        } |
        Sort-Object InterfaceMetric, InterfaceAlias
    return ($Candidates | Select-Object -First 1).IPAddress
}

function Invoke-AdbForDevice {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    if ($Serial) {
        & adb -s $Serial @Args
    } else {
        & adb @Args
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

$LanIp = Get-LanIp
if (-not $LanIp) {
    throw "Could not detect LAN IP. Use ipconfig and pass URL manually in the app."
}

$Devices = adb devices | Select-String -Pattern "`tdevice$"
$HasAdbDevice = [bool]$Devices
$ApiUrl = "http://$LanIp`:$BackendPort"

if ($UseAdbReverse) {
    if (-not $HasAdbDevice) {
        throw "No adb device connected. Enable USB debugging or run without -UseAdbReverse."
    }
    Invoke-AdbForDevice reverse "tcp:$BackendPort" "tcp:$BackendPort"
    $ApiUrl = "http://127.0.0.1:$BackendPort"
}

if ($HasAdbDevice -and -not $SkipInstall) {
    Invoke-AdbForDevice install -r $ApkPath
}
if ($HasAdbDevice -and $CleanData) {
    Invoke-AdbForDevice shell pm clear $PackageName
}
if ($HasAdbDevice) {
    $Activity = (Invoke-AdbForDevice shell cmd package resolve-activity --brief $PackageName | Select-Object -Last 1).Trim()
    if ($Activity) {
        Invoke-AdbForDevice shell am start -n $Activity
    }
}

Write-Host "PHYSICAL_ANDROID_DEV_READY"
Write-Host "Backend on PC: http://127.0.0.1:$BackendPort"
Write-Host "Use this API URL in the app: $ApiUrl"
Write-Host "If it times out over Wi-Fi, allow TCP $BackendPort in Windows Firewall or use: -UseAdbReverse"
Write-Host "Backend logs: $BackendOut"
Write-Host "Stop backend: powershell -ExecutionPolicy Bypass -File .\scripts\run_physical_android_dev.ps1 -StopBackend"
