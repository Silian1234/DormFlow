param(
    [string]$Serial = "emulator-5554",
    [string]$PackageName = "org.dormflow.dormflow",
    [string]$ApkPath = "",
    [int]$BackendPort = 8765,
    [string]$HeadmanCode = "SMOKE",
    [switch]$KeepBackend
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Python = Join-Path $Root ".venv310\Scripts\python.exe"
$RunDir = Join-Path $Root "qa-results\android-e2e-smoke"

if (-not (Test-Path $Python)) {
    throw "Python venv not found: $Python"
}

if (-not $ApkPath) {
    $ApkPath = Join-Path $Root "apps\android\bin\dormflow-1.0.0-arm64-v8a_armeabi-v7a-debug.apk"
}
if (-not (Test-Path $ApkPath)) {
    throw "APK not found: $ApkPath"
}

New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$DbPath = Join-Path $RunDir "backend.sqlite3"
$BackendOut = Join-Path $RunDir "backend_stdout.log"
$BackendErr = Join-Path $RunDir "backend_stderr.log"
$AppLog = Join-Path $RunDir "app_logcat.txt"
Remove-Item -LiteralPath $DbPath,$BackendOut,$BackendErr,$AppLog -ErrorAction SilentlyContinue

function Invoke-Adb {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)
    & adb -s $Serial @Args
}

function Save-Screenshot {
    param([string]$Name)
    $Path = Join-Path $RunDir $Name
    cmd /c "adb -s $Serial exec-out screencap -p > `"$Path`""
}

function Tap-Ratio {
    param([double]$X, [double]$Y)
    $sizeLine = (Invoke-Adb shell wm size | Select-Object -First 1)
    if ($sizeLine -match "(\d+)x(\d+)") {
        $width = [int]$Matches[1]
        $height = [int]$Matches[2]
    } else {
        $width = 1080
        $height = 2340
    }
    Invoke-Adb shell input tap ([int]($width * $X)) ([int]($height * $Y)) | Out-Null
}

$Backend = $null
try {
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

    $ready = $false
    for ($i = 0; $i -lt 50; $i++) {
        Start-Sleep -Milliseconds 200
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2
            if ($health.status -eq "ok" -and $health.service -eq "dormflow") {
                $ready = $true
                break
            }
        } catch {
        }
        if ($Backend.HasExited) {
            break
        }
    }
    if (-not $ready) {
        Get-Content $BackendErr -ErrorAction SilentlyContinue
        throw "Backend did not start on port $BackendPort"
    }

    Invoke-Adb install -r $ApkPath | Out-File (Join-Path $RunDir "install.txt") -Encoding utf8
    Invoke-Adb shell pm clear $PackageName | Out-File (Join-Path $RunDir "pm_clear.txt") -Encoding utf8
    Invoke-Adb logcat -c | Out-Null
    $Activity = (Invoke-Adb shell cmd package resolve-activity --brief $PackageName | Select-Object -Last 1).Trim()
    if (-not $Activity) {
        throw "Unable to resolve activity for $PackageName"
    }
    $Activity | Out-File (Join-Path $RunDir "activity.txt") -Encoding utf8
    Invoke-Adb shell am start -n $Activity | Out-Null
    Start-Sleep -Seconds 7
    Save-Screenshot "01_auth_login.png"

    Tap-Ratio 0.704 0.282
    Start-Sleep -Milliseconds 600
    Save-Screenshot "02_register_empty.png"

    $Login = "user$([DateTimeOffset]::Now.ToUnixTimeMilliseconds())"
    $Login | Out-File (Join-Path $RunDir "login.txt") -Encoding utf8
    Tap-Ratio 0.204 0.331
    Invoke-Adb shell input text $Login | Out-Null
    Tap-Ratio 0.208 0.402
    Invoke-Adb shell input text "password1" | Out-Null
    Tap-Ratio 0.208 0.469
    Invoke-Adb shell input text "E2EUser" | Out-Null
    Tap-Ratio 0.194 0.545
    Invoke-Adb shell input text "3" | Out-Null
    Tap-Ratio 0.495 0.545
    Invoke-Adb shell input text "4" | Out-Null
    Tap-Ratio 0.792 0.545
    Invoke-Adb shell input text "418" | Out-Null
    Save-Screenshot "03_register_filled.png"

    Invoke-Adb shell input keyevent 111 | Out-Null
    Start-Sleep -Milliseconds 500
    Tap-Ratio 0.5 0.938
    Start-Sleep -Seconds 6
    Save-Screenshot "04_after_submit.png"

    $AppPid = (Invoke-Adb shell pidof -s $PackageName).Trim()
    if ($AppPid) {
        Invoke-Adb logcat -d -t 1200 --pid $AppPid | Out-File $AppLog -Encoding utf8
    }

    $DbCheckScript = Join-Path $RunDir "check_db.py"
    @'
import sqlite3
import sys
from pathlib import Path

db = Path(sys.argv[1])
connection = sqlite3.connect(db)
connection.row_factory = sqlite3.Row
users = [dict(row) for row in connection.execute("SELECT email, name, room, role FROM users ORDER BY id")]
sessions = connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
print(f"users={len(users)} sessions={sessions}")
for user in users:
    print(user)
if not users or sessions < 1:
    raise SystemExit(2)
'@ | Set-Content -Path $DbCheckScript -Encoding utf8
    $Summary = & $Python $DbCheckScript $DbPath
    if ($LASTEXITCODE -ne 0) {
        throw "DB verification failed"
    }
    $Summary | Out-File (Join-Path $RunDir "db_summary.txt") -Encoding utf8

    $BackendLog = Get-Content $BackendOut -ErrorAction SilentlyContinue
    if (-not ($BackendLog | Select-String -SimpleMatch "POST /auth/register")) {
        throw "Backend did not receive POST /auth/register"
    }
    if (-not ($BackendLog | Select-String -SimpleMatch "GET /state")) {
        throw "Backend did not receive GET /state after registration"
    }

    if (Test-Path $AppLog) {
        $Fatal = Get-Content $AppLog | Select-String -Pattern "Traceback|FATAL EXCEPTION|ANR|CRASH" -CaseSensitive:$false
        if ($Fatal) {
            $Fatal | Select-Object -First 40
            throw "App log contains fatal errors"
        }
    }

    Write-Output "ANDROID_E2E_OK"
    Write-Output "Artifacts: $RunDir"
    Write-Output $Summary
} finally {
    if ($Backend -and -not $Backend.HasExited -and -not $KeepBackend) {
        Stop-Process -Id $Backend.Id -Force
    }
}
