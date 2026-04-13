from AppKit import NSScreen

def get_all_monitors_info():
    """
    연결된 모든 모니터의 사용 가능한 영역(메뉴바, Dock 제외)을 반환합니다.
    """
    monitors = []
    for screen in NSScreen.screens():
        # frame: 전체 영역, visibleFrame: 유효 영역
        frame = screen.visibleFrame()
        # macOS 좌표계는 하단 왼쪽이 (0,0)이지만, 일반적인 윈도우 제어 API는 상단 왼쪽을 기준으로 함
        # 여기서는 단순히 (x, y, width, height) 튜플을 반환
        info = {
            "x": int(frame.origin.x),
            "y": int(frame.origin.y),
            "width": int(frame.size.width),
            "height": int(frame.size.height)
        }
        monitors.append(info)
    return monitors

if __name__ == "__main__":
    # 직접 실행 시 결과 출력 (테스트용)
    print(get_all_monitors_info())
