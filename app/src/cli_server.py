import sys
import socket
import logging
from AppKit import NSWorkspace
from app.src.coordinate_calculator import calculate_window_position
from app.src.monitor_info import get_all_monitors_info
from app.src.window_manager import get_active_window_object, set_window_bounds, get_window_bounds, is_accessibility_trusted

# 로깅 설정 (표준 출력)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def execute_command(mode):
    logging.info(f"--- [명령 실행: {mode}] ---")
    
    # 1. 권한 확인
    if not is_accessibility_trusted():
        logging.error("macOS '접근성(Accessibility)' 권한이 없습니다!")
        return

    # 2. 모니터 정보 가져오기
    monitors = get_all_monitors_info()
    if not monitors:
        logging.error("모니터 정보를 가져올 수 없습니다.")
        return
        
    # 3. 활성 창 및 현재 좌표 가져오기
    target_window = get_active_window_object()
    if not target_window:
        logging.error("활성 창을 찾을 수 없습니다. (현재 앱: %s)" % NSWorkspace.sharedWorkspace().frontmostApplication().localizedName())
        return
        
    current_bounds = get_window_bounds(target_window)
    if not current_bounds:
        logging.error("현재 창의 좌표 정보를 가져올 수 없습니다.")
        return
    
    # 4. 현재 창이 어느 모니터에 있는지 판별
    cx, cy = current_bounds[0] + current_bounds[2] // 2, current_bounds[1] + current_bounds[3] // 2
    target_monitor = monitors[0]
    for m in monitors:
        if m['x'] <= cx < m['x'] + m['width'] and m['y'] <= cy < m['y'] + m['height']:
            target_monitor = m
            break
            
    logging.info(f"대상 모니터: {target_monitor}")
    screen_size = (target_monitor['width'], target_monitor['height'])
    
    # 5. 새로운 좌표 계산
    x_rel, y_rel, width, height = calculate_window_position(screen_size, mode)
    
    # 모니터 절대 좌표로 변환
    final_x = x_rel + target_monitor['x']
    final_y = y_rel + target_monitor['y']

    # 6. 창 크기 적용
    success = set_window_bounds(target_window, final_x, final_y, width, height)
    if success:
        logging.info(f"성공: {mode} -> ({final_x}, {final_y}, {width}, {height})")
    else:
        logging.error("창 제어 API 호출 실패")

if __name__ == "__main__":
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', 9999))
            s.listen()
            logging.info("CLI 테스트 전용 소켓 서버 시작됨 (Port: 9999)")
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024).decode().strip()
                    if data:
                        logging.info(f"[네트워크 명령 수신] {data}")
                        execute_command(data)
    except KeyboardInterrupt:
        logging.info("서버 종료")
    except Exception as e:
        logging.error(f"서버 오류: {e}")
