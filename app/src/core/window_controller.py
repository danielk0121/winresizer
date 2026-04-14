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
        
        # 3. 명령 처리
        if mode == "open_accessibility":
            import subprocess
            subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])
            return

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

        # 8. 모니터 간 이동 로직: 이미 해당 위치라면 다음 모니터로 이동 (Restore 상태로)
        # tolerance를 50으로 높여서 브라우저의 최소 크기 제한이나 섀도우 영향을 커버함
        is_already_aligned = is_similar(current_bounds, expected_abs, tolerance=50)
        
        # [엣지 판정 보강] 브라우저 최소 크기 제한 등으로 인해 크기가 다르더라도 
        # 요청한 방향의 경계에 이미 도달해 있다면 정렬된 것으로 간주함
        if not is_already_aligned:
            curr_x, curr_y, curr_w, curr_h = current_bounds
            exp_x, exp_y, exp_w, exp_h = expected_abs
            
            # x, y 좌표가 유사(tolerance=20)하고, 창의 크기가 타겟보다 작지 않은 경우(최소 크기 제한 고려)
            if "left" in mode:
                if abs(curr_x - exp_x) <= 20 and abs(curr_y - exp_y) <= 20:
                    is_already_aligned = True
            elif "right" in mode:
                # 우측 끝(x+w)이 일치하거나, 화면 밖으로 짤린 경우(x+w > exp_x+exp_w) 정렬된 것으로 간주
                curr_right = curr_x + curr_w
                exp_right = exp_x + exp_w
                if (abs(curr_right - exp_right) <= 20 or curr_right > exp_right + 5) and abs(curr_y - exp_y) <= 20:
                    is_already_aligned = True
            elif "top" in mode:
                if abs(curr_x - exp_x) <= 20 and abs(curr_y - exp_y) <= 20:
                    is_already_aligned = True
            elif "bottom" in mode:
                # 하단 끝(y+h)이 일치하거나, 화면 밖으로 짤린 경우 정렬된 것으로 간주
                curr_bottom = curr_y + curr_h
                exp_bottom = exp_y + exp_h
                if (abs(curr_bottom - exp_bottom) <= 20 or curr_bottom > exp_bottom + 5) and abs(curr_x - exp_x) <= 20:
                    is_already_aligned = True
            elif mode == "maximize":
                # 전체화면은 그냥 x, y만 맞으면 (크기는 작을 수 없으므로) 정렬된 것으로 간주 가능성이 높음
                if abs(curr_x - exp_x) <= 20 and abs(curr_y - exp_y) <= 20:
                    is_already_aligned = True

        if is_already_aligned:
            index = monitor_list.index(target_monitor)
            next_monitor = monitor_list[(index + 1) % len(monitor_list)]
            
            # 저장된 원래 상태 가져오기
            saved_state = get_saved_window_state(target_window)
            if not saved_state:
                saved_state = current_bounds  # 저장된 상태가 없으면 현재 상태라도 사용

            # saved_state가 어느 모니터에 있었는지 판별
            saved_monitor = monitor_list[0]
            s_center_x = saved_state[0] + saved_state[2] // 2
            s_center_y = saved_state[1] + saved_state[3] // 2
            for m in monitor_list:
                if m['x'] <= s_center_x < m['x'] + m['width'] and \
                   m['y'] <= s_center_y < m['y'] + m['height']:
                    saved_monitor = m
                    break

            # 원래 모니터에서의 상대적 좌표 유지하며 다음 모니터로 이동
            rel_x = saved_state[0] - saved_monitor['x']
            rel_y = saved_state[1] - saved_monitor['y']
            
            # 새 좌표 (다음 모니터의 크기에 맞춰 크기 제한)
            new_w = min(saved_state[2], next_monitor['width'] - gap * 2)
            new_h = min(saved_state[3], next_monitor['height'] - gap * 2)
            new_x = next_monitor['x'] + rel_x
            new_y = next_monitor['y'] + rel_y
            
            # 새 모니터 범위를 벗어나지 않도록 보정 (선택 사항)
            new_x = max(next_monitor['x'] + gap, min(new_x, next_monitor['x'] + next_monitor['width'] - new_w - gap))
            new_y = max(next_monitor['y'] + gap, min(new_y, next_monitor['y'] + next_monitor['height'] - new_h - gap))

            set_window_bounds(target_window, new_x, new_y, new_w, new_h)
            logger.info(f"Window already at {mode} position. Moving to next monitor in restore state.")
            
            # 다음 정렬을 위해 함수 종료
            try:
                pid = active_app.processIdentifier()
                activate_application(pid)
            except Exception: pass
            return

        # 9. 최종 좌표 적용
        target_x = x_relative + target_monitor['x']
        target_y = y_relative + target_monitor['y']
        set_window_bounds(target_window, target_x, target_y, width, height)
        
        # [버그 수정] 실제 적용된 크기를 확인하여 우측/하단 정렬 시 화면 짤림 보정 (Re-anchoring)
        actual_bounds = get_window_bounds(target_window)
        if actual_bounds:
            curr_x, curr_y, curr_w, curr_h = actual_bounds
            needs_reanchor = False
            new_x, new_y = curr_x, curr_y
            
            # 우측 정렬 계열 (right_half, right_1/3, right_2/3, right_custom, top_right, bottom_right)
            if "right" in mode:
                expected_right = target_monitor['x'] + target_monitor['width'] - gap
                actual_right = curr_x + curr_w
                # 실제 우측 끝이 예상보다 5px 이상 화면 밖으로 나갔을 때만 보정
                if actual_right > expected_right + 5:
                    new_x = expected_right - curr_w
                    needs_reanchor = True
            
            # 하단 정렬 계열 (bottom_half, bottom_left, bottom_right, bottom_custom)
            if "bottom" in mode:
                expected_bottom = target_monitor['y'] + target_monitor['height'] - gap
                actual_bottom = curr_y + curr_h
                # 실제 하단 끝이 예상보다 5px 이상 화면 밖으로 나갔을 때만 보정
                if actual_bottom > expected_bottom + 5:
                    new_y = expected_bottom - curr_h
                    needs_reanchor = True
            
            if needs_reanchor:
                logger.info(f"Re-anchoring window due to size constraints: ({curr_x}, {curr_y}) -> ({new_x}, {new_y})")
                set_window_bounds(target_window, new_x, new_y, curr_w, curr_h)

        # 10. 포커스 유실 방지
        try:
            pid = active_app.processIdentifier()
            activate_application(pid)
        except Exception:
            pass
            
        logger.info(f"Window command completed: {mode}")
    except Exception as e: 
        logger.error(f"Error during window command execution: {e}", exc_info=True)
