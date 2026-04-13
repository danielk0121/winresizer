from utils.logger import logger
from AppKit import NSWorkspace
from core.coordinate_calculator import calculate_window_position
from core.monitor_info import get_all_monitors_info
from core.window_manager import (
    get_active_window_object, set_window_bounds, get_window_bounds, 
    is_accessibility_trusted, activate_application, save_window_state, get_saved_window_state, clear_window_state
)
from utils.helpers import apply_gap
from core import config_manager
from core.smart_cycler import determine_next_mode

def execute_window_command(mode):
    """
    지정된 모드(예: '좌측_절반', '복구' 등)에 따라 활성 윈도우의 크기와 위치를 조정합니다.
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
        if mode == "복구":
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
        relative_bounds = (current_bounds[0] - target_monitor['x'], current_bounds[1] - target_monitor['y'], current_bounds[2], current_bounds[3])

        # 6. 스마트 순환 로직
        if mode == "다음_디스플레이":
            index = monitor_list.index(target_monitor)
            next_monitor = monitor_list[(index + 1) % len(monitor_list)]
            new_x = next_monitor['x'] + relative_bounds[0]
            new_y = next_monitor['y'] + relative_bounds[1]
            set_window_bounds(target_window, new_x, new_y, min(current_bounds[2], next_monitor['width']), min(current_bounds[3], next_monitor['height']))
            return
            
        next_mode = determine_next_mode(mode, relative_bounds, screen_size, gap)

        # 7. 좌표 계산 및 적용
        result_coords = calculate_window_position(screen_size, next_mode)
        x_relative, y_relative, width, height = apply_gap(*result_coords, gap)
        set_window_bounds(target_window, x_relative + target_monitor['x'], y_relative + target_monitor['y'], width, height)
        
        # 8. 포커스 유실 방지
        try:
            pid = active_app.processIdentifier()
            activate_application(pid)
        except Exception:
            pass
            
        logger.info(f"Window command completed: {next_mode}")
    except Exception as e: 
        logger.error(f"Error during window command execution: {e}", exc_info=True)
