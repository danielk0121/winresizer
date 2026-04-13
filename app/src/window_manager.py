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

def 활성_윈도우_객체_가져오기():
    """
    현재 가장 앞에 있는(Frontmost) 애플리케이션의 활성화된 윈도우 객체를 반환합니다.
    """
    활성_앱 = NSWorkspace.sharedWorkspace().frontmostApplication()
    피드 = 활성_앱.processIdentifier()
    앱_객체 = AXUIElementCreateApplication(피드)
    
    결과, 윈도우_객체 = AXUIElementCopyAttributeValue(앱_객체, kAXFocusedWindowAttribute, None)
    if 결과 == 0:
        return 윈도우_객체
    return None

def 윈도우_크기_및_위치_변경(윈도우_객체, x, y, 너비, 높이):
    """
    지정된 윈도우 객체의 위치와 크기를 변경합니다.
    """
    if not 윈도우_객체:
        return False
        
    위치 = CGPointMake(x, y)
    크기 = CGSizeMake(너비, 높이)
    
    # 위치 설정
    AXUIElementSetAttributeValue(윈도우_객체, kAXPositionAttribute, 위치)
    # 크기 설정
    AXUIElementSetAttributeValue(윈도우_객체, kAXSizeAttribute, 크기)
    return True

if __name__ == "__main__":
    # 간단한 테스트: 현재 활성 창의 위치를 약간 옮김
    대상 = 활성_윈도우_객체_가져오기()
    if 대상:
        print("활성 윈도우를 찾았습니다. 위치를 조정합니다.")
        윈도우_크기_및_위치_변경(대상, 100, 100, 800, 600)
    else:
        print("활성 윈도우를 찾을 수 없습니다. (접근성 권한 확인 필요)")
