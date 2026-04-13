from AppKit import NSWorkspace
from ApplicationServices import (
    AXUIElementCreateApplication, 
    AXUIElementCopyAttributeValue, 
    AXUIElementSetAttributeValue,
    AXValueCreate,
    AXValueGetValue,
    AXIsProcessTrusted,
    kAXFocusedWindowAttribute,
    kAXPositionAttribute,
    kAXSizeAttribute,
    kAXValueCGPointType,
    kAXValueCGSizeType
)
from Quartz.CoreGraphics import CGPointMake, CGSizeMake, CGPoint, CGSize

# 윈도우 객체별 원래 상태 저장소 (복구용)
# 메모리 누수 방지를 위해 실제 서비스에서는 정리가 필요할 수 있으나, 현재는 딕셔너리로 관리
_window_history = {}

def save_window_state(window_object, bounds):
    """
    윈도우의 현재 상태를 이력에 저장합니다. (이미 저장된 경우 무시하여 최초 상태 유지)
    """
    if window_object not in _window_history:
        _window_history[window_object] = bounds

def get_saved_window_state(window_object):
    """
    저장된 윈도우의 원래 상태를 반환합니다.
    """
    return _window_history.get(window_object)

def clear_window_state(window_object):
    """
    윈도우의 저장된 상태를 삭제합니다.
    """
    if window_object in _window_history:
        del _window_history[window_object]

def is_accessibility_trusted():
    """
    현재 프로세스가 접근성(Accessibility) 권한을 가지고 있는지 확인합니다.
    """
    return AXIsProcessTrusted()

def get_active_window_object():
    """
    현재 가장 앞에 있는(Frontmost) 애플리케이션의 활성화된 윈도우 객체를 반환합니다.
    """
    active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
    if not active_app:
        return None
        
    pid = active_app.processIdentifier()
    app_object = AXUIElementCreateApplication(pid)
    
    result, window_object = AXUIElementCopyAttributeValue(app_object, kAXFocusedWindowAttribute, None)
    if result == 0:
        return window_object
    return None

def get_window_bounds(window_object):
    """
    지정된 윈도우 객체의 현재 위치와 크기(x, y, w, h)를 반환합니다.
    """
    if not window_object:
        return None
        
    # 1. 위치 가져오기
    res_pos, ax_pos = AXUIElementCopyAttributeValue(window_object, kAXPositionAttribute, None)
    if res_pos != 0: return None
    
    # PyObjC: AXValueGetValue는 (성공여부, 결과값) 튜플을 반환하며 세 번째 인자는 None이어야 함
    ok_pos, pos = AXValueGetValue(ax_pos, kAXValueCGPointType, None)
    if not ok_pos: return None
    
    # 2. 크기 가져오기
    res_size, ax_size = AXUIElementCopyAttributeValue(window_object, kAXSizeAttribute, None)
    if res_size != 0: return None
    
    ok_size, size = AXValueGetValue(ax_size, kAXValueCGSizeType, None)
    if not ok_size: return None
    
    return (pos.x, pos.y, size.width, size.height)

def set_window_bounds(window_object, x, y, width, height):
    """
    지정된 윈도우 객체의 위치와 크기를 변경합니다.
    """
    if not window_object:
        return False
        
    # 1. 위치 설정 (x, y)
    pos = CGPointMake(x, y)
    ax_pos = AXValueCreate(kAXValueCGPointType, pos)
    res_pos = AXUIElementSetAttributeValue(window_object, kAXPositionAttribute, ax_pos)
    
    # 2. 크기 설정 (w, h)
    size = CGSizeMake(width, height)
    ax_size = AXValueCreate(kAXValueCGSizeType, size)
    res_size = AXUIElementSetAttributeValue(window_object, kAXSizeAttribute, ax_size)
    
    if res_pos != 0 or res_size != 0:
        # 0이 아니면 실패 (kAXErrorSuccess = 0)
        # 34: kAXErrorCannotComplete (권한 문제 또는 창이 응답 없음)
        # -25204: kAXErrorAttributeUnsupported
        import logging
        logging.error(f"[API 오류] 위치설정: {res_pos}, 크시설정: {res_size} (창: {window_object})")
        return False
        
    return True

def activate_application(pid):
    """
    주어진 PID를 가진 애플리케이션을 최상위로 올리고 포커스를 부여합니다.
    창 이동 후 포커스가 유실되는 현상을 방지하기 위해 사용합니다.
    """
    from AppKit import NSRunningApplication, NSApplicationActivateIgnoringOtherApps
    app = NSRunningApplication.runningApplicationWithProcessIdentifier_(pid)
    if app:
        # NSApplicationActivateIgnoringOtherApps (2) 옵션으로 강제 활성화
        app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
        return True
    return False

if __name__ == "__main__":
    if is_accessibility_trusted():
        target = get_active_window_object()
        if target:
            print(f"현재 창 정보: {get_window_bounds(target)}")
