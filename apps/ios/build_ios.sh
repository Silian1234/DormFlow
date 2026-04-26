#!/usr/bin/env bash
set -euo pipefail

APP_TITLE="${DORMFLOW_IOS_TITLE:-DormFlow}"
BUNDLE_ID="${DORMFLOW_IOS_BUNDLE_ID:-org.dormflow.dormflow}"
IOS_PLATFORM="${DORMFLOW_IOS_PLATFORM:-auto}"
PROJECT_SLUG="$(printf "%s" "$APP_TITLE" | tr "[:upper:]" "[:lower:]")"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
IOS_DIR="$ROOT_DIR/apps/ios"
VENV_DIR="$ROOT_DIR/.venv-ios"
BUILD_DIR="$IOS_DIR/.build"
APP_DIR="$BUILD_DIR/app"
PROJECT_PARENT="$IOS_DIR/xcode"
PROJECT_DIR="$PROJECT_PARENT/$PROJECT_SLUG-ios"
ICON_SOURCE="$ROOT_DIR/assets/ios/icon.png"
LAUNCH_SOURCE="$ROOT_DIR/assets/ios/launch.png"

fail() {
  echo "error: $*" >&2
  exit 1
}

cd "$ROOT_DIR"

case "$APP_TITLE" in
  *[!A-Za-z0-9_]*)
    fail "DORMFLOW_IOS_TITLE must contain only letters, digits, or underscores."
    ;;
esac

if [[ "$(uname -s)" != "Darwin" ]]; then
  fail "iOS build is supported only on macOS with Xcode."
fi

if ! command -v xcodebuild >/dev/null 2>&1; then
  fail "xcodebuild was not found. Install Xcode and Command Line Tools first."
fi

PY_BIN="${PYTHON_BIN:-python3.11}"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  PY_BIN="python3"
fi
command -v "$PY_BIN" >/dev/null 2>&1 || fail "python3 was not found."

if [[ ! -d "$VENV_DIR" ]]; then
  "$PY_BIN" -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r "$IOS_DIR/requirements.txt"

TOOLCHAIN="$(command -v toolchain || true)"
[[ -n "$TOOLCHAIN" ]] || fail "kivy-ios toolchain command was not installed into $VENV_DIR."

mkdir -p "$BUILD_DIR" "$PROJECT_PARENT"
case "$APP_DIR" in
  "$IOS_DIR"/.build/*) rm -rf "$APP_DIR" ;;
  *) fail "refusing to delete unexpected app staging path: $APP_DIR" ;;
esac
mkdir -p "$APP_DIR/dormflow"

rsync -a --delete \
  --exclude "__pycache__/" \
  --exclude "*.pyc" \
  "$ROOT_DIR/dormflow/" "$APP_DIR/dormflow/"
cp "$ROOT_DIR/main.py" "$APP_DIR/main.py"
cp "$ROOT_DIR/requirements.txt" "$APP_DIR/requirements.txt"

BUILD_ARGS=(build python3 kivy)
case "$IOS_PLATFORM" in
  auto) ;;
  iphoneos-arm64|iphonesimulator-arm64|iphonesimulator-x86_64)
    BUILD_ARGS+=(--platform "$IOS_PLATFORM")
    ;;
  all)
    BUILD_ARGS+=(--platform iphoneos-arm64 --platform iphonesimulator-arm64 --platform iphonesimulator-x86_64)
    ;;
  *)
    fail "unsupported DORMFLOW_IOS_PLATFORM=$IOS_PLATFORM"
    ;;
esac

"$TOOLCHAIN" "${BUILD_ARGS[@]}"

if [[ -d "$PROJECT_DIR" ]]; then
  "$TOOLCHAIN" update "$PROJECT_DIR"
else
  (cd "$PROJECT_PARENT" && "$TOOLCHAIN" create "$APP_TITLE" "$APP_DIR")
fi

[[ -d "$PROJECT_DIR" ]] || fail "expected Xcode project directory was not created: $PROJECT_DIR"

PBXPROJ="$(find "$PROJECT_DIR" -name project.pbxproj -print -quit)"
if [[ -n "$PBXPROJ" ]]; then
  python - "$PBXPROJ" "$BUNDLE_ID" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
bundle_id = sys.argv[2]
text = path.read_text(encoding="utf-8")
text = re.sub(
    r"PRODUCT_BUNDLE_IDENTIFIER = [^;]+;",
    f"PRODUCT_BUNDLE_IDENTIFIER = {bundle_id};",
    text,
)
path.write_text(text, encoding="utf-8")
PY
fi

if [[ -f "$ICON_SOURCE" ]]; then
  "$TOOLCHAIN" icon "$PROJECT_DIR" "$ICON_SOURCE" || echo "warning: icon generation skipped"
fi

if [[ -f "$LAUNCH_SOURCE" ]]; then
  "$TOOLCHAIN" launchimage "$PROJECT_DIR" "$LAUNCH_SOURCE" || echo "warning: launch image generation skipped"
fi

INFO_PLIST="$(find "$PROJECT_DIR" -name Info.plist -print -quit)"
if [[ -n "$INFO_PLIST" ]]; then
  /usr/libexec/PlistBuddy -c "Add :NSAppTransportSecurity dict" "$INFO_PLIST" 2>/dev/null || true
  /usr/libexec/PlistBuddy -c "Set :NSAppTransportSecurity:NSAllowsArbitraryLoads true" "$INFO_PLIST" 2>/dev/null \
    || /usr/libexec/PlistBuddy -c "Add :NSAppTransportSecurity:NSAllowsArbitraryLoads bool true" "$INFO_PLIST"
fi

echo "iOS project is ready:"
echo "  $PROJECT_DIR"
echo "Open it in Xcode:"
echo "  open \"$PROJECT_DIR\"/*.xcodeproj"
