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
    # Quartz(Top-Left 0,0) 좌표계에서 메인 모니터의 상단은 항상 0입니다.
    # 하지만 visibleFrame은 메뉴바(보통 25px)를 제외하므로, 
    # y=0 위치의 메뉴바가 있다면 visibleFrame.origin.y + height 가 frame.height 보다 작게 됩니다.
    
    monitors = []
    for screen in screens:
        v_frame = screen.visibleFrame()  # Dock/MenuBar 제외 유효 영역
        s_frame = screen.frame()         # 전체 화면 영역 (좌표축 계산용)
        
        # AppKit (0,0) 하단왼쪽 -> Quartz (0,0) 상단왼쪽 변환
        # Quartz_Y = Main_Monitor_Frame_Height - (AppKit_Y + Height)
        # 여기서 Main_Monitor_Frame_Height는 NSScreen.screens()[0].frame().size.height 입니다.
        main_height = screens[0].frame().size.height
        
        # 실제 Quartz 좌표상의 Y (상단 기준)
        quartz_y = main_height - (v_frame.origin.y + v_frame.size.height)
        
        # 보조 모니터의 경우, 메인 모니터 프레임 밖으로 나갈 수 있으므로 정밀 보정
        # 만약 메인 모니터보다 위에 있는 보조 모니터라면 quartz_y가 음수가 될 수도 있음
        
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
