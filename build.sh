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

# libintl.8.dylib의 원본 경로
LIBINTL_SRC="/opt/homebrew/lib/libintl.8.dylib"

# 1. libintl.8.dylib 복사 (필요한 모든 곳에 배치)
cp "$LIBINTL_SRC" "$MACOS_PATH/"
cp "$LIBINTL_SRC" "$FRAMEWORKS_PATH/" 2>/dev/null || true
cp "$LIBINTL_SRC" "$RESOURCES_PATH/" 2>/dev/null || true

# 1-1. 아이콘 파일도 Frameworks에 복사 (helpers.py 대응)
cp "app/src/ui/tray_icon.png" "$FRAMEWORKS_PATH/" 2>/dev/null || true

# 2. Python 프레임워크 내부에도 복사 (dlopen 실패 해결의 핵심)
PYTHON_FW_PATH=$(find "$FRAMEWORKS_PATH" -name "Versions" -type d | head -n 1)
if [ -d "$PYTHON_FW_PATH" ]; then
    find "$PYTHON_FW_PATH" -maxdepth 2 -type d | while read -r version_dir; do
        if [ -f "$version_dir/Python" ]; then
            echo "Copying libintl to $version_dir"
            cp "$LIBINTL_SRC" "$version_dir/"
            # 복사된 라이브러리 ID 수정
            install_name_tool -id "@loader_path/libintl.8.dylib" "$version_dir/libintl.8.dylib"
        fi
    done
fi

# 3. 모든 바이너리들의 libintl ID 및 참조 경로 수정
echo "Updating binaries..."
find "$APP_PATH" -type f \( -perm +111 -o -name "*.so" -o -name "*.dylib" -o -name "Python" \) | while read -r bin; do
    # libintl 자체라면 ID만 수정하고 패스
    if [[ "$bin" == *"libintl.8.dylib" ]]; then
        install_name_tool -id "@loader_path/libintl.8.dylib" "$bin" 2>/dev/null || true
        continue
    fi
    
    # libintl 참조 경로를 @loader_path로 강제 치환
    # 가능한 모든 패턴에 대해 시도 (Homebrew 경로나 rpath 등)
    install_name_tool -change "/opt/homebrew/opt/gettext/lib/libintl.8.dylib" "@loader_path/libintl.8.dylib" "$bin" 2>/dev/null || true
    install_name_tool -change "/opt/homebrew/lib/libintl.8.dylib" "@loader_path/libintl.8.dylib" "$bin" 2>/dev/null || true
    install_name_tool -change "@rpath/libintl.8.dylib" "@loader_path/libintl.8.dylib" "$bin" 2>/dev/null || true
    
    # rpath 추가
    install_name_tool -add_rpath "@loader_path/." "$bin" 2>/dev/null || true
done

# 코드 재서명 (Ad-hoc)
echo "Resigning App Bundle..."
codesign --force --deep --sign - "$APP_PATH"

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
