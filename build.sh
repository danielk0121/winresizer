#!/bin/bash
set -e

# Go to script directory to ensure relative paths work
cd "$(dirname "$0")"

echo "Building App Bundle..."
# .spec 파일로 빌드 (info_plist 등 세부 설정 포함)
./app/venv/bin/pyinstaller --noconfirm --log-level=WARN WinResizer.spec

echo "Fixing rpath for macOS bundle..."
APP_PATH="dist/WinResizer.app"
MACOS_PATH="$APP_PATH/Contents/MacOS"
FRAMEWORKS_PATH="$APP_PATH/Contents/Frameworks"
RESOURCES_PATH="$APP_PATH/Contents/Resources"

# libintl.8.dylib 복사 (필요한 모든 곳에 배치)
cp /opt/homebrew/lib/libintl.8.dylib "$MACOS_PATH/"
cp /opt/homebrew/lib/libintl.8.dylib "$FRAMEWORKS_PATH/" 2>/dev/null || true
cp /opt/homebrew/lib/libintl.8.dylib "$RESOURCES_PATH/" 2>/dev/null || true

# 메인 실행 파일 rpath 수정
echo "Updating main executable rpath..."
install_name_tool -add_rpath "@loader_path/." "$MACOS_PATH/WinResizer" 2>/dev/null || true
install_name_tool -change "@rpath/libintl.8.dylib" "@loader_path/libintl.8.dylib" "$MACOS_PATH/WinResizer" 2>/dev/null || true

# Python 바이너리 rpath 수정 (경로를 동적으로 찾음)
echo "Updating Python binaries rpath..."
find "$APP_PATH" -name "Python" -type f | while read -r python_bin; do
    install_name_tool -add_rpath "@loader_path/." "$python_bin" 2>/dev/null || true
    # 상위 폴더(MacOS)에 있는 libintl을 찾을 수 있도록 추가 rpath 설정
    install_name_tool -add_rpath "@loader_path/../../MacOS" "$python_bin" 2>/dev/null || true
    install_name_tool -change "@rpath/libintl.8.dylib" "@loader_path/libintl.8.dylib" "$python_bin" 2>/dev/null || true
done

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
echo "Finalizing App..."
