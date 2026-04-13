from pynput import keyboard
from app.src.coordinate_calculator import 창_위치_계산
from app.src.monitor_info import 모든_모니터_정보_가져오기
from app.src.window_manager import 활성_윈도우_객체_가져오기, 윈도우_크기_및_위치_변경

# 전역 단축키 설정 (Option + Command 조합)
단축키_매핑 = {
    '<alt>+<cmd>+<left>': '좌측_절반',
    '<alt>+<cmd>+<right>': '우측_절반',
    '<alt>+<cmd>+c': '중앙_고정'
}

def 실행_명령(모드):
    """
    지정된 모드에 따라 현재 활성 창의 크기를 조정합니다.
    """
    print(f"[{모드}] 명령 실행 시도 중...")
    
    # 1. 모니터 정보 가져오기 (첫 번째 모니터 기준 우선 구현)
    모니터들 = 모든_모니터_정보_가져오기()
    if not 모니터들:
        print("모니터 정보를 가져올 수 없습니다.")
        return
        
    메인_모니터 = 모니터들[0] # 실제로는 창이 위치한 모니터를 찾아야 함
    화면_크기 = (메인_모니터['너비'], 메인_모니터['높이'])
    
    # 2. 새로운 좌표 계산
    x, y, 너비, 높이 = 창_위치_계산(화면_크기, 모드)
    
    # macOS 좌표 보정 (모니터 원점 기준)
    x += 메인_모니터['x']
    # macOS Quartz API는 화면 상단이 0이므로 별도의 Y축 반전 보정이 필요할 수 있음
    # 여기서는 간단히 origin.y를 더함
    y += 메인_모니터['y']

    # 3. 활성 창 제어
    대상_창 = 활성_윈도우_객체_가져오기()
    if 대상_창:
        윈도우_크기_및_위치_변경(대상_창, x, y, 너비, 높이)
        print(f"창 크기 조정 완료: {너비}x{높이} @ ({x}, {y})")
    else:
        print("활성 창을 찾을 수 없습니다. (접근성 권한이 필요합니다)")

def 단축키_콜백():
    """
    pynput Global Hotkey 핸들러를 생성합니다.
    """
    with keyboard.GlobalHotKeys({
        키: lambda m=모드: 실행_명령(m) for 키, 모드 in 단축키_매핑.items()
    }) as h:
        print("윈도우 리사이저 실행 중... (Ctrl+C로 종료)")
        h.join()

if __name__ == "__main__":
    try:
        단축키_콜백()
    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
