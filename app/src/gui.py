import sys
import socket
import logging
import os
import datetime
from AppKit import NSWorkspace
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy, QScrollArea, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from pynput import keyboard
from app.src.coordinate_calculator import calculate_window_position
from app.src.monitor_info import get_all_monitors_info
from app.src.window_manager import get_active_window_object, set_window_bounds, get_window_bounds, is_accessibility_trusted
from app.src.config_manager import load_config, save_config

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

# 설정 및 상태 관리
CONFIG = load_config()
HOTKEY_CONFIG = CONFIG['shortcuts']
SETTINGS = CONFIG['settings']
WINDOW_HISTORY = {} # 전역 창 위치 히스토리

def is_nearly_equal(b1, b2, tol=20): # 오차 범위를 20으로 늘려 메뉴바/Dock 보정
    if not b1 or not b2: return False
    return all(abs(a - b) <= tol for a, b in zip(b1, b2))

def find_monitor(bounds, monitors):
    if not bounds or not monitors: return 0
    cx, cy = bounds[0] + bounds[2] // 2, bounds[1] + bounds[3] // 2
    for i, m in enumerate(monitors):
        if m['x'] <= cx < m['x'] + m['width'] and m['y'] <= cy < m['y'] + m['height']:
            return i
    return 0

def apply_gap(x, y, w, h, gap):
    return (x + gap, y + gap, w - 2 * gap, h - 2 * gap)

def execute_window_command(mode):
    try:
        logging.info(f"--- [명령 시작: {mode}] ---")
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if not active_app: return
        
        app_name = active_app.localizedName()
        if app_name in SETTINGS.get('ignore_apps', []):
            logging.info(f"[무시] {app_name} 제외 대상")
            return
            
        monitors = get_all_monitors_info()
        target_window = get_active_window_object()
        if not target_window:
            logging.error(f"활성 창 객체를 가져오지 못했습니다. 앱: {app_name}")
            return
            
        current_bounds = get_window_bounds(target_window)
        if not current_bounds: return
        
        win_id, gap = hash(target_window), SETTINGS.get('gap', 5)
        
        if mode == "복구":
            if win_id in WINDOW_HISTORY:
                set_window_bounds(target_window, *WINDOW_HISTORY[win_id])
                del WINDOW_HISTORY[win_id]
                logging.info(f"[{app_name}] 위치 복구 완료")
            return
        
        if mode in ["다음_디스플레이", "이전_디스플레이"]:
            idx = find_monitor(current_bounds, monitors)
            n_idx = (idx + 1 if mode == "다음_디스플레이" else idx - 1) % len(monitors)
            if idx != n_idx:
                m, nm = monitors[idx], monitors[n_idx]
                new_x = nm['x'] + (current_bounds[0] - m['x'])
                new_y = nm['y'] + (current_bounds[1] - m['y'])
                set_window_bounds(target_window, new_x, new_y, min(current_bounds[2], nm['width']), min(current_bounds[3], nm['height']))
                logging.info(f"[{app_name}] 디스플레이 {n_idx}로 이동")
            return

        if win_id not in WINDOW_HISTORY: WINDOW_HISTORY[win_id] = current_bounds

        idx = find_monitor(current_bounds, monitors)
        m = monitors[idx]
        screen_size = (m['width'], m['height'])
        local_bounds = (current_bounds[0] - m['x'], current_bounds[1] - m['y'], current_bounds[2], current_bounds[3])
        c_size = SETTINGS.get('center_size', {'width': 1200, 'height': 800})
        
        def get_gap_pos(mode_name):
            res = calculate_window_position(screen_size, mode_name)
            if mode_name == "중앙_고정":
                res = ((screen_size[0] - c_size['width']) // 2, (screen_size[1] - c_size['height']) // 2, c_size['width'], c_size['height'])
            return apply_gap(*res, gap)

        next_mode = mode
        if mode == "좌측_절반":
            if is_nearly_equal(local_bounds, get_gap_pos("좌측_절반")): next_mode = "좌측_1/3"
            elif is_nearly_equal(local_bounds, get_gap_pos("좌측_1/3")): next_mode = "좌측_2/3"
        elif mode == "우측_절반":
            if is_nearly_equal(local_bounds, get_gap_pos("우측_절반")): next_mode = "우측_1/3"
            elif is_nearly_equal(local_bounds, get_gap_pos("우측_1/3")): next_mode = "우측_2/3"

        res_coords = calculate_window_position(screen_size, next_mode)
        if next_mode == "중앙_고정":
            res_coords = ((screen_size[0] - c_size['width']) // 2, (screen_size[1] - c_size['height']) // 2, c_size['width'], c_size['height'])
        
        x_rel, y_rel, w, h = apply_gap(*res_coords, gap)
        final_x, final_y = x_rel + m['x'], y_rel + m['y']
        
        logging.info(f"[{app_name}] 적용 모드: {next_mode}, 목표 좌표: ({final_x}, {final_y}, {w}, {h})")
        if set_window_bounds(target_window, final_x, final_y, w, h):
            logging.info("창 크기 조정 성공")
        else:
            logging.error("창 크기 조정 실패 (API 호출 결과 0 아님)")
            
    except Exception as e:
        logging.error(f"명령 실행 중 오류: {e}", exc_info=True)

class CommandServerThread(QThread):
    commandReceived = pyqtSignal(str)
    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('127.0.0.1', 9999)) # 127.0.0.1 고정
                s.listen()
                logging.info("네트워크 명령 서버 대기 중 (Port: 9999)")
                while True:
                    conn, _ = s.accept()
                    with conn:
                        data = conn.recv(1024).decode().strip()
                        if data:
                            logging.info(f"[네트워크] 명령 수신: {data}")
                            self.commandReceived.emit(data)
        except Exception as e: logging.error(f"서버 오류: {e}")

class HotkeyListenerThread(QThread):
    def run(self):
        if not is_accessibility_trusted(): return
        mapping = {c['pynput']: lambda m=c['mode']: execute_window_command(m) for c in HOTKEY_CONFIG.values() if c['pynput']}
        logging.info("단축키 리스너 시작됨")
        with keyboard.GlobalHotKeys(mapping) as h: h.join()

class WinResizerPreferences(QWidget):
    def __init__(self):
        super().__init__()
        self.ht = HotkeyListenerThread()
        self.ht.start()
        self.cs = CommandServerThread()
        self.cs.commandReceived.connect(execute_window_command)
        self.cs.start()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("WinResizer 설정")
        self.setMinimumSize(400, 500)
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")

        layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("WinResizer 설정")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("margin-bottom: 20px; color: #00aaff;")
        layout.addWidget(title)

        # 간격(Gap) 설정
        gap_layout = QHBoxLayout()
        gap_label = QLabel("창 간격 (Gap):")
        gap_label.setFont(QFont("Arial", 12))
        
        self.gap_spin = QSpinBox()
        self.gap_spin.setRange(0, 100)
        self.gap_spin.setValue(SETTINGS.get('gap', 5))
        self.gap_spin.setSuffix(" px")
        self.gap_spin.setStyleSheet("""
            QSpinBox {
                background-color: #3c3f41;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                min-width: 80px;
            }
        """)
        self.gap_spin.valueChanged.connect(self.update_gap)
        
        gap_layout.addWidget(gap_label)
        gap_layout.addWidget(self.gap_spin)
        gap_layout.addStretch()
        layout.addLayout(gap_layout)

        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # 종료 버튼
        btn_quit = QPushButton("앱 종료")
        btn_quit.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                border: none;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_quit.clicked.connect(QApplication.instance().quit)
        layout.addWidget(btn_quit)

    def update_gap(self, value):
        SETTINGS['gap'] = value
        save_config(CONFIG)
        logging.info(f"창 간격 설정 변경: {value}px")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
