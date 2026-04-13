from AppKit import NSScreen

def get_all_monitors_info():
    """
    연결된 모든 모니터의 사용 가능한 영역(메뉴바, Dock 제외)을 반환합니다.
    macOS의 AppKit(하단 기준) 좌표를 Accessibility API(상단 기준) 좌표로 변환합니다.
    """
    screens = NSScreen.screens()
    if not screens:
        return []

    # 0번 모니터(메인 모니터)의 전체 높이를 기준으로 Y좌표를 변환함
    main_frame = screens[0].frame()
    main_height = main_frame.size.height
    
    monitors = []
    for screen in screens:
        v_frame = screen.visibleFrame()  # Dock/MenuBar 제외 유효 영역
        s_frame = screen.frame()         # 전체 화면 영역 (Y좌표 계산용)
        
        # AppKit (0,0) 하단왼쪽 -> Quartz (0,0) 상단왼쪽 변환
        # Quartz_Y = Main_Height - (AppKit_Y + Height)
        quartz_y = main_height - (v_frame.origin.y + v_frame.size.height)
        
        info = {
            "x": int(v_frame.origin.x),
            "y": int(quartz_y),
            "width": int(v_frame.size.width),
            "height": int(v_frame.size.height)
        }
        monitors.append(info)
    return monitors

if __name__ == "__main__":
    # 직접 실행 시 결과 출력 (테스트용)
    print(get_all_monitors_info())
