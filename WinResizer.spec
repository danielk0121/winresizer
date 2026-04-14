# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['app/src/main.py'],
    pathex=['app/src'],
    binaries=[],
    datas=[
        ('app/src/ui/tray_icon.png', 'app/src/ui'),
        ('app/src/templates', 'app/src/templates'),
        ('app/src/static', 'app/src/static'),
        ('app/src/config', 'app/src/config'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WinResizer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['app/src/ui/icon.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WinResizer',
)
app = BUNDLE(
    coll,
    name='WinResizer.app',
    icon='app/src/ui/icon.icns',
    bundle_identifier='com.winresizer.app',
    info_plist={
        'CFBundleShortVersionString': '1.0.0',
        'LSUIElement': True,
        'NSAccessibilityUsageDescription': 'WinResizer는 단축키로 창 위치와 크기를 조절하기 위해 손쉬운 사용 권한이 필요합니다.',
        'NSAppleEventsUsageDescription': 'WinResizer는 활성 창 제어를 위해 이 권한이 필요합니다.',
    },
)
