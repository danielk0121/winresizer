import sys
import socket
import logging
import threading
import time
from AppKit import NSWorkspace
from pynput import keyboard
from app.src.coordinate_calculator import calculate_window_position
from app.src.monitor_info import get_all_monitors_info
from app.src.window_manager import get_active_window_object, set_window_bounds, get_window_bounds, is_accessibility_trusted

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

def execute_command(mode):
    logging.info(f"--- [명령 실행: {mode}] ---")
    
    if not is_accessibility_trusted():
        logging.error("macOS 접근성(Accessibility) 권한이 없습니다! 시스템 설정에서 터미널의 권한을 확인해 주세요.")
        return

    monitors = get_all_monitors_info()
    target_window = get_active_window_object()
    if not target_window:
        logging.error("활성 창을 찾을 수 없습니다. (현재 앱: %s)" % NSWorkspace.sharedWorkspace().frontmostApplication().localizedName())
        return
        
    current_bounds = get_window_bounds(target_window)
    if not current_bounds:
        logging.error("현재 창의 좌표를 가져올 수 없습니다.")
        return
    
    # 모니터 판별
    cx, cy = current_bounds[0] + current_bounds[2] // 2, current_bounds[1] + current_bounds[3] // 2
    target_monitor = monitors[0]
    for m in monitors:
        if m['x'] <= cx < m['x'] + m['width'] and m['y'] <= cy < m['y'] + m['height']:
            target_monitor = m
            break
            
    # 디스플레이 이동 처리
    if mode == "다음_디스플레이":
        idx = monitors.index(target_monitor)
        nm = monitors[(idx + 1) % len(monitors)]
        new_x = nm['x'] + (current_bounds[0] - target_monitor['x'])
        new_y = nm['y'] + (current_bounds[1] - target_monitor['y'])
        set_window_bounds(target_window, new_x, new_y, min(current_bounds[2], nm['width']), min(current_bounds[3], nm['height']))
        logging.info(f"디스플레이 이동 시도: {idx} -> {(idx+1)%len(monitors)}")
        return

    screen_size = (target_monitor['width'], target_monitor['height'])
    x_rel, y_rel, w, h = calculate_window_position(screen_size, mode)
    
    final_x = x_rel + target_monitor['x']
    final_y = y_rel + target_monitor['y']

    logging.info(f"적용 좌표: ({final_x}, {final_y}, {w}, {h})")
    if set_window_bounds(target_window, final_x, final_y, w, h):
        logging.info("성공!")
    else:
        logging.error("실패!")

def server_loop():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('localhost', 9999))
            s.listen()
            logging.info("CLI 소켓 서버 대기 중 (Port: 9999)...")
            while True:
                conn, _ = s.accept()
                with conn:
                    data = conn.recv(1024).decode().strip()
                    if data:
                        logging.info(f"[네트워크 명령 수신] {data}")
                        # 메인 스레드가 아니어도 CLI 환경에서는 직접 실행 가능
                        execute_command(data)
    except Exception as e:
        logging.error(f"서버 오류: {e}")

if __name__ == "__main__":
    # 소켓 서버를 별도 스레드에서 시작
    threading.Thread(target=server_loop, daemon=True).start()
    
    # 단축키 리스너 (강력한 조합: Ctrl+Alt+Cmd+방향키)
    logging.info("윈도우 리사이저 실행 중 (Ctrl+C로 종료)...")
    try:
        with keyboard.GlobalHotKeys({
            '<ctrl>+<alt>+<cmd>+<left>': lambda: execute_command('좌측_절반'),
            '<ctrl>+<alt>+<cmd>+<right>': lambda: execute_command('우측_절반'),
            '<ctrl>+<alt>+<cmd>+<up>': lambda: execute_command('다음_디스플레이'),
            '<ctrl>+<alt>+<cmd>+c': lambda: execute_command('중앙_고정')
        }) as h:
            h.join()
    except KeyboardInterrupt:
        logging.info("종료 중...")
