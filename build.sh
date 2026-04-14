#!/bin/bash
set -e

# Go to script directory to ensure relative paths work
cd "$(dirname "$0")"

echo "Building App Bundle..."
# .spec 파일로 빌드 (info_plist 등 세부 설정 포함)
./app/venv/bin/pyinstaller --noconfirm --log-level=WARN WinResizer.spec

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

echo "Fixing rpath for macOS bundle..."
# 스텁 수정 (에러 메시지 억제)
install_name_tool -add_rpath "@loader_path/." dist/WinResizer.app/Contents/Frameworks/Python 2>/dev/null || true
install_name_tool -change "@rpath/libintl.8.dylib" "@loader_path/libintl.8.dylib" dist/WinResizer.app/Contents/Frameworks/Python 2>/dev/null || true

# 실제 라이브러리 수정 (Python 3.14 기준 경로)
REAL_PYTHON="dist/WinResizer.app/Contents/Frameworks/Python.framework/Versions/3.14/Python"
if [ -f "$REAL_PYTHON" ]; then
    # 이미 존재하는 경우 에러가 발생하므로 2>/dev/null로 출력을 숨김
    install_name_tool -add_rpath "@loader_path/." "$REAL_PYTHON" 2>/dev/null || true
    install_name_tool -add_rpath "@loader_path/../../.." "$REAL_PYTHON" 2>/dev/null || true
    install_name_tool -change "@rpath/libintl.8.dylib" "@loader_path/../../../libintl.8.dylib" "$REAL_PYTHON" 2>/dev/null || true
fi

echo "Finalizing App..."