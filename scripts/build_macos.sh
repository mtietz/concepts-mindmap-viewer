#!/bin/bash
set -euo pipefail

cd "$(dirname "$0")/.."

args=(
  --clean
  --noconfirm
  --windowed
  --onedir
  --name "Concepts Mindmap Viewer"
  --osx-bundle-identifier "com.mtietz.concepts-mindmap-viewer"
  --target-architecture "${MACOS_TARGET_ARCH:-universal2}"
  --icon "packaging/AppIcon.icns"
  --add-data "static:static"
  --osx-entitlements-file "packaging/entitlements.plist"
)

if [[ -n "${APPLE_SIGNING_IDENTITY:-}" ]]; then
  args+=(--codesign-identity "$APPLE_SIGNING_IDENTITY")
fi

python3 -m PyInstaller "${args[@]}" desktop.py

app="dist/Concepts Mindmap Viewer.app"
version="${APP_VERSION:-0.1.0}"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $version" "$app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $version" "$app/Contents/Info.plist" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c "Set :CFBundleVersion $version" "$app/Contents/Info.plist"
codesign --force --options runtime --entitlements packaging/entitlements.plist \
  --sign "${APPLE_SIGNING_IDENTITY:--}" "$app"
codesign --verify --deep --strict "$app"

echo "Built: $app"
