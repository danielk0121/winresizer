import sys
import socket
import logging
import threading
import os
import datetime
from AppKit import NSWorkspace
from pynput import keyboard
from app.src.coordinate_calculator import calculate_window_position
from app.src.monitor_info import get_all_monitors_info
from app.src.window_manager import get_active_window_object, set_window_bounds, get_window_bounds, is_accessibility_trusted

# 로깅 설정
LOG_DIR = "log"
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)

# yyyyMMdd_HHmmss KST 형식의 타임스탬프 생성
kst_now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"winresizer_{kst_now}_KST.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, log_filename), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

def is_nearly_equal(b1, b2, tol=20):
    if not b1 or not b2: return False
    return all(abs(a - b) <= tol for a, b in zip(b1, b2))

def apply_gap(x, y, w, h, gap=5):
    return (x + gap, y + gap, w - 2 * gap, h - 2 * gap)

def execute_command(mode):
    logging.info(f"--- [명령 실행: {mode}] ---")
    if not is_accessibility_trusted():
        logging.error("macOS 접근성 권한이 없습니다!")
        return
        
    monitors = get_all_monitors_info()
    target_window = get_active_window_object()
    if not target_window: return
        
    current_bounds = get_window_bounds(target_window)
    if not current_bounds: return
    
    cx, cy = current_bounds[0] + current_bounds[2] // 2, current_bounds[1] + current_bounds[3] // 2
    target_monitor = monitors[0]
    for m in monitors:
        if m['x'] <= cx < m['x'] + m['width'] and m['y'] <= cy < m['y'] + m['height']:
            target_monitor = m
            break
            
    if mode == "다음_디스플레이":
        idx = monitors.index(target_monitor)
        nm = monitors[(idx + 1) % len(monitors)]
        new_x = nm['x'] + (current_bounds[0] - target_monitor['x'])
        new_y = nm['y'] + (current_bounds[1] - target_monitor['y'])
        set_window_bounds(target_window, new_x, new_y, min(current_bounds[2], nm['width']), min(current_bounds[3], nm['height']))
        return

    screen_size = (target_monitor['width'], target_monitor['height'])
    local_bounds = (current_bounds[0] - target_monitor['x'], current_bounds[1] - target_monitor['y'], current_bounds[2], current_bounds[3])
    gap = 5

    def get_gap_pos(mode_name):
        res = calculate_window_position(screen_size, mode_name)
        return apply_gap(*res, gap)

    next_mode = mode
    if mode == "좌측_절반":
        if is_nearly_equal(local_bounds, get_gap_pos("좌측_절반")): next_mode = "좌측_1/3"
        elif is_nearly_equal(local_bounds, get_gap_pos("좌측_1/3")): next_mode = "좌측_2/3"
    elif mode == "우측_절반":
        if is_nearly_equal(local_bounds, get_gap_pos("우측_절반")): next_mode = "우측_1/3"
        elif is_nearly_equal(local_bounds, get_gap_pos("우측_1/3")): next_mode = "우측_2/3"

    res_coords = calculate_window_position(screen_size, next_mode)
    x_rel, y_rel, w, h = apply_gap(*res_coords, gap)
    final_x, final_y = x_rel + target_monitor['x'], y_rel + target_monitor['y']

    logging.info(f"좌표 적용 시도: ({final_x}, {final_y}, {w}, {h}) [모드: {next_mode}]")
    set_window_bounds(target_window, final_x, final_y, w, h)

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 9999))
        s.listen()
        logging.info("CLI 소켓 서버 시작됨 (127.0.0.1:9999)")
        while True:
            conn, _ = s.accept()
            with conn:
                data = conn.recv(1024).decode().strip()
                if data:
                    logging.info(f"[소켓 명령] {data}")
                    execute_command(data)

if __name__ == "__main__":
    threading.Thread(target=start_server, daemon=True).start()
    logging.info("윈도우 리사이저 리스너 실행 중...")
    with keyboard.GlobalHotKeys({
        '<ctrl>+<alt>+<cmd>+<left>': lambda: execute_command('좌측_절반'),
        '<ctrl>+<alt>+<cmd>+<right>': lambda: execute_command('우측_절반'),
        '<ctrl>+<alt>+<cmd>+<up>': lambda: execute_command('다음_디스플레이')
    }) as h:
        h.join()
