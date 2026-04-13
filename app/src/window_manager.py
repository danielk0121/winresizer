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
    
    pos = CGPoint()
    AXValueGetValue(ax_pos, kAXValueCGPointType, pos)
    
    # 2. 크기 가져오기
    res_size, ax_size = AXUIElementCopyAttributeValue(window_object, kAXSizeAttribute, None)
    if res_size != 0: return None
    
    size = CGSize()
    AXValueGetValue(ax_size, kAXValueCGSizeType, size)
    
    return (pos.x, pos.y, size.width, size.height)

def set_window_bounds(window_object, x, y, width, height):
    """
    지정된 윈도우 객체의 위치와 크기를 변경합니다.
    """
    if not window_object:
        return False
        
    # 1. 위치 설정 (CGPoint -> AXValue)
    pos = CGPointMake(x, y)
    ax_pos = AXValueCreate(kAXValueCGPointType, pos)
    res_pos = AXUIElementSetAttributeValue(window_object, kAXPositionAttribute, ax_pos)
    
    # 2. 크기 설정 (CGSize -> AXValue)
    size = CGSizeMake(width, height)
    ax_size = AXValueCreate(kAXValueCGSizeType, size)
    res_size = AXUIElementSetAttributeValue(window_object, kAXSizeAttribute, ax_size)
    
    # AXError 결과 확인 (0: kAXErrorSuccess)
    if res_pos != 0 or res_size != 0:
        print(f"경고: 창 제어 API 호출 실패 (위치 에러: {res_pos}, 크기 에러: {res_size})")
        return False
        
    return True

if __name__ == "__main__":
    if not is_accessibility_trusted():
        print("접근성 권한이 없습니다. 시스템 설정에서 권한을 부여해 주세요.")
    else:
        target = get_active_window_object()
        if target:
            print(f"현재 창 정보: {get_window_bounds(target)}")
