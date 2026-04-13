import os
import subprocess
import pytest
import shutil

@pytest.fixture(scope="session", autouse=True)
def run_build_script():
    """앱 번들 및 DMG 생성을 위한 빌드 스크립트 실행"""
    build_script = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../build.sh'))
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    
    # Run the build script
    result = subprocess.run(['bash', build_script], cwd=project_root, capture_output=True, text=True)
    assert result.returncode == 0, f"Build script failed:\n{result.stderr}\n{result.stdout}"
    
    yield

def test_app_bundle_creation():
    """앱 번들 빌드 검증: 필수 내부 구조 확인"""
    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dist/WinResizer.app'))
    
    assert os.path.exists(app_path), "WinResizer.app 디렉토리가 생성되지 않았습니다."
    
    # Contents/MacOS 검증
    macos_dir = os.path.join(app_path, 'Contents/MacOS')
    assert os.path.exists(macos_dir)
    assert os.path.exists(os.path.join(macos_dir, 'WinResizer')), "실행 가능한 바이너리가 없습니다."
    
    # Contents/Resources 검증
    resources_dir = os.path.join(app_path, 'Contents/Resources')
    assert os.path.exists(resources_dir)
    assert os.path.exists(os.path.join(resources_dir, 'icon.icns')), "아이콘 파일이 번들에 포함되지 않았습니다."
    
    # Info.plist 검증
    info_plist = os.path.join(app_path, 'Contents/Info.plist')
    assert os.path.exists(info_plist)

def test_dmg_creation_and_mount():
    """DMG 생성 및 구조 검증: 마운트 후 내부 구성 요소 확인"""
    dmg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../dist/WinResizer.dmg'))
    
    assert os.path.exists(dmg_path), "WinResizer.dmg 파일이 생성되지 않았습니다."
    
    # 마운트 테스트
    mount_point = "/Volumes/WinResizer"
    
    # 이미 마운트되어 있다면 언마운트
    if os.path.exists(mount_point):
        subprocess.run(['hdiutil', 'detach', mount_point, '-force'])
        
    # DMG 마운트
    attach_result = subprocess.run(['hdiutil', 'attach', dmg_path, '-mountpoint', mount_point, '-nobrowse'], capture_output=True)
    assert attach_result.returncode == 0, f"DMG 마운트 실패: {attach_result.stderr}"
    
    try:
        # 마운트된 내용물 검사
        assert os.path.exists(os.path.join(mount_point, 'WinResizer.app')), "DMG 내부에 WinResizer.app이 없습니다."
        assert os.path.exists(os.path.join(mount_point, 'Applications')), "DMG 내부에 Applications 심볼릭 링크가 없습니다."
    finally:
        # 테스트 종료 후 반드시 언마운트
        detach_result = subprocess.run(['hdiutil', 'detach', mount_point, '-force'])
        assert detach_result.returncode == 0, "DMG 언마운트 실패"

def test_accessibility_permission_isolation_manual_instruction():
    """접근성 권한 독립성 검증 (수동 안내)"""
    print("\n\n[보안 검증 안내]")
    print("시스템 레벨 권한 분리는 자동화 테스트로 완벽히 검증할 수 없습니다.")
    print("dist/WinResizer.app 을 직접 더블 클릭하여 실행하세요.")
    print("실행 시 '손쉬운 사용' 권한 요청이 '터미널'이 아닌 'WinResizer' 앱 자체로 나타나는지 반드시 육안으로 확인해야 합니다.\n")
