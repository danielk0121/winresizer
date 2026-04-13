from AppKit import NSScreen

def 모든_모니터_정보_가져오기():
    """
    연결된 모든 모니터의 사용 가능한 영역(메뉴바, Dock 제외)을 반환합니다.
    """
    모니터들 = []
    for 화면 in NSScreen.screens():
        # frame: 전체 영역, visibleFrame: 유효 영역
        영역 = 화면.visibleFrame()
        # macOS 좌표계는 하단 왼쪽이 (0,0)이지만, 일반적인 윈도우 제어 API는 상단 왼쪽을 기준으로 함
        # 여기서는 단순히 (x, y, width, height) 튜플을 반환
        정보 = {
            "x": int(영역.origin.x),
            "y": int(영역.origin.y),
            "너비": int(영역.size.width),
            "높이": int(영역.size.height)
        }
        모니터들.append(정보)
    return 모니터들

if __name__ == "__main__":
    # 직접 실행 시 결과 출력 (테스트용)
    print(모든_모니터_정보_가져오기())
