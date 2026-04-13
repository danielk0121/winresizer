#!/bin/bash
set -e

# Go to script directory to ensure relative paths work
cd "$(dirname "$0")"

echo "Building App Bundle..."
# PyInstaller command
./app/venv/bin/pyinstaller --noconfirm --log-level=WARN \
    --windowed \
    --name="WinResizer" \
    --icon="app/src/ui/icon.icns" \
    --add-data="app/src/ui/tray_icon.png:app/src/ui" \
    --osx-bundle-identifier "com.winresizer.app" \
    --paths="app/src" \
    app/src/main.py

echo "Creating DMG..."
mkdir -p dist/dmg
cp -r dist/WinResizer.app dist/dmg/
ln -s /Applications dist/dmg/Applications

if command -v create-dmg > /dev/null; then
    create-dmg \
      --volname "WinResizer Installer" \
      --volicon "app/src/ui/icon.icns" \
      --window-pos 200 120 \
      --window-size 600 400 \
      --icon-size 100 \
      --icon "WinResizer.app" 175 120 \
      --hide-extension "WinResizer.app" \
      --app-drop-link 425 120 \
      "dist/WinResizer.dmg" \
      "dist/dmg/" || true
else
    echo "create-dmg not found, using hdiutil..."
    rm -f dist/WinResizer.dmg
    hdiutil create -volname "WinResizer" -srcfolder dist/dmg -ov -format UDZO dist/WinResizer.dmg
fi

rm -rf dist/dmg

echo "Build Complete!"