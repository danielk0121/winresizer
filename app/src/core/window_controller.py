from utils.logger import logger
from AppKit import NSWorkspace
from core.coordinate_calculator import calculate_window_position
from core.monitor_info import get_all_monitors_info
from core.window_manager import (
    get_active_window_object, set_window_bounds, get_window_bounds, 
    is_accessibility_trusted, activate_application, save_window_state, get_saved_window_state, clear_window_state
)
from utils.helpers import apply_gap, is_similar
from core import config_manager

def parse_custom_mode(mode):
    """
    커스텀 비율 모드 문자열을 파싱합니다.
    'left_custom:75' → ('left', 75)
    커스텀 모드가 아니면 None 반환.
    """
    if not isinstance(mode, str) or "_custom:" not in mode:
        return None
    try:
        direction, pct_str = mode.split("_custom:")
        return (direction, int(pct_str))
    except (ValueError, AttributeError):
        return None


def is_valid_custom_mode(mode):
    """
    커스텀 비율 모드의 유효성을 검사합니다.
    유효 조건: 커스텀 모드이고 비율이 1~100 정수.
    """
    parsed = parse_custom_mode(mode)
    if parsed is None:
        return False
    _, pct = parsed
    return 1 <= pct <= 100


def execute_window_command(mode):
    """
    지정된 모드(예: 'left_half', 'maximize' 등)에 따라 활성 윈도우의 크기와 위치를 조정합니다.
    """
    try:
        logger.debug(f"Executing window command: {mode}")
        
        # 1. 권한 확인
        if not is_accessibility_trusted():
            logger.warning("macOS Accessibility permission is not granted.")
            return

        # 2. 활성 앱 및 윈도우 가져오기
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if not active_app:
            logger.debug("Active application not found")
            return
            
        app_name = active_app.localizedName()
        config = config_manager.get_config()
        settings = config.get('settings', {})
        
        if app_name in settings.get('ignore_apps', []):
            logger.debug(f"Ignoring app: {app_name}")
            return
            
        target_window = get_active_window_object()
        if not target_window:
            logger.debug("Active window object not found")
            return
            
        current_bounds = get_window_bounds(target_window)
        if not current_bounds:
            logger.debug("Failed to get window bounds")
            return
            
        gap = settings.get('gap', 5)
        
        # 3. 복구 모드 처리
        if mode == "복구" or mode == "restore":
            saved_state = get_saved_window_state(target_window)
            if saved_state:
                set_window_bounds(target_window, *saved_state)
                clear_window_state(target_window)
                logger.info("Window restored successfully")
            else:
                logger.info("No saved state for this window.")
            return
        
        # 4. 현재 상태 저장 (복구용, 최초 1회)
        save_window_state(target_window, current_bounds)
        
        # 5. 모니터 판별
        monitor_list = get_all_monitors_info()
        center_x = current_bounds[0] + current_bounds[2] // 2
        center_y = current_bounds[1] + current_bounds[3] // 2
        
        target_monitor = monitor_list[0]
        for monitor in monitor_list:
            if monitor['x'] <= center_x < monitor['x'] + monitor['width'] and \
               monitor['y'] <= center_y < monitor['y'] + monitor['height']:
                target_monitor = monitor
                break
        
        screen_size = (target_monitor['width'], target_monitor['height'])

        # 6. 다음 디스플레이 이동 (명시적 명령)
        if mode == "다음_디스플레이" or mode == "next_display":
            index = monitor_list.index(target_monitor)
            next_monitor = monitor_list[(index + 1) % len(monitor_list)]
            relative_x = current_bounds[0] - target_monitor['x']
            relative_y = current_bounds[1] - target_monitor['y']
            set_window_bounds(target_window, 
                              next_monitor['x'] + relative_x, 
                              next_monitor['y'] + relative_y, 
                              min(current_bounds[2], next_monitor['width']), 
                              min(current_bounds[3], next_monitor['height']))
            return

        # 7. 좌표 계산
        # 기존 테스트 코드와 호환성을 위해 apply_gap을 사용하는 예전 방식으로 복구하되, 모니터 이동 로직만 결합
        result_coords = calculate_window_position(screen_size, mode)
        x_relative, y_relative, width, height = apply_gap(*result_coords, gap)
        expected_abs = (x_relative + target_monitor['x'],
                        y_relative + target_monitor['y'],
                        width,
                        height)

        # 8. 모니터 간 이동 로직: 이미 해당 위치라면 다음 모니터로 타겟 변경
        if is_similar(current_bounds, expected_abs):
            index = monitor_list.index(target_monitor)
            target_monitor = monitor_list[(index + 1) % len(monitor_list)]
            screen_size = (target_monitor['width'], target_monitor['height'])
            result_coords = calculate_window_position(screen_size, mode)
            x_relative, y_relative, width, height = apply_gap(*result_coords, gap)
            logger.info(f"Window already at {mode} position. Moving to next monitor.")

        # 9. 최종 좌표 적용
        set_window_bounds(target_window,
                          x_relative + target_monitor['x'],
                          y_relative + target_monitor['y'],
                          width, height)
        
        # 10. 포커스 유실 방지
        try:
            pid = active_app.processIdentifier()
            activate_application(pid)
        except Exception:
            pass
            
        logger.info(f"Window command completed: {mode}")
    except Exception as e: 
        logger.error(f"Error during window command execution: {e}", exc_info=True)
