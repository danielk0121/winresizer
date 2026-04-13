from AppKit import NSWorkspace
from Quartz import (
    AXUIElementCreateApplication, 
    AXUIElementCopyAttributeValue, 
    AXUIElementSetAttributeValue,
    kAXFocusedWindowAttribute,
    kAXPositionAttribute,
    kAXSizeAttribute,
    CGPointMake,
    CGSizeMake
)

def get_active_window_object():
    """
    현재 가장 앞에 있는(Frontmost) 애플리케이션의 활성화된 윈도우 객체를 반환합니다.
    """
    active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
    pid = active_app.processIdentifier()
    app_object = AXUIElementCreateApplication(pid)
    
    result, window_object = AXUIElementCopyAttributeValue(app_object, kAXFocusedWindowAttribute, None)
    if result == 0:
        return window_object
    return None

def set_window_bounds(window_object, x, y, width, height):
    """
    지정된 윈도우 객체의 위치와 크기를 변경합니다.
    """
    if not window_object:
        return False
        
    position = CGPointMake(x, y)
    size = CGSizeMake(width, height)
    
    # 위치 설정
    AXUIElementSetAttributeValue(window_object, kAXPositionAttribute, position)
    # 크기 설정
    AXUIElementSetAttributeValue(window_object, kAXSizeAttribute, size)
    return True

if __name__ == "__main__":
    # 간단한 테스트: 현재 활성 창의 위치를 약간 옮김
    target = get_active_window_object()
    if target:
        print("활성 윈도우를 찾았습니다. 위치를 조정합니다.")
        set_window_bounds(target, 100, 100, 800, 600)
    else:
        print("활성 윈도우를 찾을 수 없습니다. (접근성 권한 확인 필요)")
