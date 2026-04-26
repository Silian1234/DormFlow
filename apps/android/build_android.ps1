$ErrorActionPreference = "Stop"

$windowsRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))
$wslPath = "/mnt/" + $windowsRoot.Substring(0,1).ToLower() + $windowsRoot.Substring(2).Replace("\", "/")

$cmd = "PROJECT_WSL_SRC='$wslPath' bash '$wslPath/apps/android/build_android_wsl.sh'"
wsl -d Ubuntu -- bash -lc "$cmd"
