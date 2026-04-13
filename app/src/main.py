from pynput import keyboard
from app.src.coordinate_calculator import calculate_window_position
from app.src.monitor_info import get_all_monitors_info
from app.src.window_manager import get_active_window_object, set_window_bounds, is_accessibility_trusted

# 전역 단축키 설정 (Option + Command 조합)
HOTKEY_MAPPING = {
    '<alt>+<cmd>+<left>': '좌측_절반',
    '<alt>+<cmd>+<right>': '우측_절반',
    '<alt>+<cmd>+c': '중앙_고정'
}

def execute_command(mode):
    """
    지정된 모드에 따라 현재 활성 창의 크기를 조정합니다.
    """
    print(f"[{mode}] 명령 실행 시도 중...")
    
    # 1. 모니터 정보 가져오기 (첫 번째 모니터 기준 우선 구현)
    monitors = get_all_monitors_info()
    if not monitors:
        print("모니터 정보를 가져올 수 없습니다.")
        return
        
    main_monitor = monitors[0] # 실제로는 창이 위치한 모니터를 찾아야 함
    screen_size = (main_monitor['width'], main_monitor['height'])
    
    # 2. 새로운 좌표 계산
    x, y, width, height = calculate_window_position(screen_size, mode)
    
    # macOS 좌표 보정 (모니터 원점 기준)
    x += main_monitor['x']
    # macOS Quartz API는 화면 상단이 0이므로 별도의 Y축 반전 보정이 필요할 수 있음
    # 여기서는 간단히 origin.y를 더함
    y += main_monitor['y']

    # 3. 활성 창 제어
    target_window = get_active_window_object()
    if target_window:
        set_window_bounds(target_window, x, y, width, height)
        print(f"창 크기 조정 완료: {width}x{height} @ ({x}, {y})")
    else:
        print("활성 창을 찾을 수 없습니다. (접근성 권한이 필요합니다)")

def setup_hotkeys():
    """
    pynput Global Hotkey 핸들러를 생성합니다.
    """
    if not is_accessibility_trusted():
        print("=" * 60)
        print("오류: macOS '접근성(Accessibility)' 권한이 없습니다!")
        print("1. [시스템 설정 > 개인정보 보호 및 보안 > 접근성]으로 이동합니다.")
        print("2. 현재 실행 중인 '터미널' 또는 'iTerm2'의 스위치를 켭니다.")
        print("   (이미 켜져 있다면 껐다가 다시 켜보세요.)")
        print("=" * 60)
        return

    with keyboard.GlobalHotKeys({
        key: lambda m=mode: execute_command(m) for key, mode in HOTKEY_MAPPING.items()
    }) as h:
        print("윈도우 리사이저 실행 중... (Ctrl+C로 종료)")
        h.join()

if __name__ == "__main__":
    try:
        setup_hotkeys()
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
