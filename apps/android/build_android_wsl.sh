#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="${PROJECT_WSL_SRC:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
WORK_ROOT="$SOURCE_ROOT"

if ! command -v buildozer >/dev/null 2>&1; then
  echo "buildozer not found. Install: python3 -m pip install --user buildozer Cython==0.29.37"
  exit 1
fi

# Buildozer/p4a can fail on mounted Windows FS permissions; build in Linux FS.
if [[ "$SOURCE_ROOT" == /mnt/* ]]; then
  WORK_ROOT="$HOME/mobileapp"
  echo "Sync project into Linux FS: $WORK_ROOT"
  mkdir -p "$WORK_ROOT"
  rsync -a --delete \
    --exclude '.git/' \
    --exclude '.venv/' \
    --exclude '.venv310/' \
    --exclude 'qa-results/' \
    --exclude 'apps/android/.buildozer/' \
    --exclude 'apps/android/bin/' \
    "$SOURCE_ROOT/" "$WORK_ROOT/"
fi

cd "$WORK_ROOT/apps/android"

export PATH="$HOME/.local/bin:$PATH"
python3 -m pip install --user --upgrade "Cython==0.29.37"

set +e
buildozer android debug 2>&1 | tee build_latest.log
BUILD_STATUS=${PIPESTATUS[0]}
set -e

if [[ "$SOURCE_ROOT" != "$WORK_ROOT" ]]; then
  mkdir -p "$SOURCE_ROOT/apps/android/bin"
  cp -f "$WORK_ROOT/apps/android/build_latest.log" "$SOURCE_ROOT/apps/android/build_latest.log" || true
  cp -f "$WORK_ROOT/apps/android/bin/"*.apk "$SOURCE_ROOT/apps/android/bin/" || true
fi

if [[ $BUILD_STATUS -ne 0 ]]; then
  echo "Build failed. Log: $WORK_ROOT/apps/android/build_latest.log"
  exit "$BUILD_STATUS"
fi

echo "Done. APK is available in apps/android/bin/."
