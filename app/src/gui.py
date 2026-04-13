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

class HotkeyButton(QPushButton):
    hotkeyChanged = pyqtSignal(str, str) # display_name, pynput_key

    def __init__(self, display_text, config_key):
        super().__init__(display_text)
        self.config_key = config_key
        self.recording = False
        self.setMinimumHeight(35)
        self.setStyleSheet("""
            QPushButton {
                background-color: #3c3f41;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #4c5052;
            }
        """)
        self.clicked.connect(self.start_recording)

    def start_recording(self):
        self.recording = True
        self.setText("키 입력 대기 중...")
        self.setStyleSheet("background-color: #007acc; color: white; border-radius: 4px;")
        self.grabKeyboard()

    def keyPressEvent(self, event):
        if not self.recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        if key == Qt.Key_Escape:
            self.stop_recording()
            return

        modifiers = event.modifiers()
        parts = []
        display_parts = []

        if modifiers & Qt.ControlModifier:
            parts.append('<ctrl>')
            display_parts.append('⌃')
        if modifiers & Qt.AltModifier:
            parts.append('<alt>')
            display_parts.append('⌥')
        if modifiers & Qt.ShiftModifier:
            parts.append('<shift>')
            display_parts.append('⇧')
        if modifiers & Qt.MetaModifier:
            parts.append('<cmd>')
            display_parts.append('⌘')

        # 키 이름 변환
        key_name = ""
        display_name = ""
        
        if Qt.Key_Left <= key <= Qt.Key_Down:
            names = {Qt.Key_Left: 'left', Qt.Key_Right: 'right', Qt.Key_Up: 'up', Qt.Key_Down: 'down'}
            d_names = {Qt.Key_Left: '←', Qt.Key_Right: '→', Qt.Key_Up: '↑', Qt.Key_Down: '↓'}
            key_name = names.get(key)
            display_name = d_names.get(key)
        elif Qt.Key_A <= key <= Qt.Key_Z:
            key_name = chr(key).lower()
            display_name = chr(key).upper()
        elif key == Qt.Key_Space:
            key_name = "space"
            display_name = "Space"
        elif key == Qt.Key_Enter or key == Qt.Key_Return:
            key_name = "enter"
            display_name = "⏎"

        if key_name:
            parts.append(key_name)
            display_parts.append(display_name)
            
            pynput_key = "+".join(parts)
            display_text = "".join(display_parts)
            
            self.hotkeyChanged.emit(self.config_key, pynput_key)
            self.setText(display_text)
            self.stop_recording()

    def stop_recording(self):
        self.recording = False
        self.releaseKeyboard()
        self.setStyleSheet("""
            QPushButton {
                background-color: #3c3f41;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        if self.text() == "키 입력 대기 중...":
            self.setText(HOTKEY_CONFIG[self.config_key]['display'])

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
        self.setMinimumSize(450, 600)
        self.setStyleSheet("background-color: #2b2b2b; color: #ffffff;")

        main_layout = QVBoxLayout(self)
        
        # 제목
        title = QLabel("WinResizer 설정")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("margin-bottom: 10px; color: #00aaff; padding-top: 10px;")
        main_layout.addWidget(title)

        # 시스템 설정 영역 (Gap)
        settings_frame = QFrame()
        settings_frame.setStyleSheet("background-color: #333333; border-radius: 8px; margin: 5px; padding: 10px;")
        settings_layout = QVBoxLayout(settings_frame)
        
        gap_layout = QHBoxLayout()
        gap_label = QLabel("창 간격 (Gap):")
        gap_label.setFont(QFont("Arial", 11))
        
        self.gap_spin = QSpinBox()
        self.gap_spin.setRange(0, 50)
        self.gap_spin.setValue(SETTINGS.get('gap', 5))
        self.gap_spin.setSuffix(" px")
        self.gap_spin.setStyleSheet("background-color: #3c3f41; padding: 3px;")
        self.gap_spin.valueChanged.connect(self.update_gap)
        
        gap_layout.addWidget(gap_label)
        gap_layout.addWidget(self.gap_spin)
        gap_layout.addStretch()
        settings_layout.addLayout(gap_layout)
        
        # 제외 앱 설정 영역
        ignore_frame = QFrame()
        ignore_frame.setStyleSheet("background-color: #333333; border-radius: 8px; margin: 5px; padding: 10px;")
        ignore_layout = QVBoxLayout(ignore_frame)
        
        ignore_title = QLabel("제외 앱 리스트 (단축키 무시):")
        ignore_title.setFont(QFont("Arial", 11, QFont.Bold))
        ignore_layout.addWidget(ignore_title)
        
        add_layout = QHBoxLayout()
        self.ignore_input = QLineEdit()
        self.ignore_input.setPlaceholderText("앱 이름 입력 (예: Photoshop)")
        self.ignore_input.setStyleSheet("background-color: #3c3f41; padding: 5px;")
        
        btn_add = QPushButton("추가")
        btn_add.setStyleSheet("background-color: #00aaff; color: white; padding: 5px; font-weight: bold;")
        btn_add.clicked.connect(self.add_ignore_app)
        
        add_layout.addWidget(self.ignore_input)
        add_layout.addWidget(btn_add)
        ignore_layout.addLayout(add_layout)
        
        self.ignore_list_layout = QVBoxLayout()
        self.refresh_ignore_list()
        ignore_layout.addLayout(self.ignore_list_layout)
        
        main_layout.addWidget(ignore_frame)

        # 단축키 설정 영역 (Scroll Area)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        self.scroll_layout = QVBoxLayout(scroll_content)
        
        for name, cfg in HOTKEY_CONFIG.items():
            row = QHBoxLayout()
            row.addWidget(QLabel(name, styleSheet="font-size: 13px;"))
            
            btn = HotkeyButton(cfg['display'], name)
            btn.hotkeyChanged.connect(self.update_hotkey)
            row.addWidget(btn)
            self.scroll_layout.addLayout(row)
            
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # 종료 버튼
        btn_quit = QPushButton("앱 종료")
        btn_quit.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                border: none;
                color: white;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_quit.clicked.connect(QApplication.instance().quit)
        main_layout.addWidget(btn_quit)

    def add_ignore_app(self):
        app_name = self.ignore_input.text().strip()
        if app_name and app_name not in SETTINGS['ignore_apps']:
            SETTINGS['ignore_apps'].append(app_name)
            save_config(CONFIG)
            self.ignore_input.clear()
            self.refresh_ignore_list()
            logging.info(f"제외 앱 추가: {app_name}")

    def remove_ignore_app(self, app_name):
        if app_name in SETTINGS['ignore_apps']:
            SETTINGS['ignore_apps'].remove(app_name)
            save_config(CONFIG)
            self.refresh_ignore_list()
            logging.info(f"제외 앱 삭제: {app_name}")

    def refresh_ignore_list(self):
        # 기존 항목 제거
        for i in reversed(range(self.ignore_list_layout.count())):
            item = self.ignore_list_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # 레이아웃 내부 위젯들 삭제
                for j in reversed(range(item.layout().count())):
                    w = item.layout().itemAt(j).widget()
                    if w: w.deleteLater()
                self.ignore_list_layout.removeItem(item)

        # 리스트 갱신
        for app in SETTINGS.get('ignore_apps', []):
            row = QHBoxLayout()
            row.addWidget(QLabel(app))
            
            btn_del = QPushButton("X")
            btn_del.setFixedSize(20, 20)
            btn_del.setStyleSheet("background-color: #e74c3c; color: white; border-radius: 10px; font-size: 10px;")
            btn_del.clicked.connect(lambda checked, a=app: self.remove_ignore_app(a))
            
            row.addWidget(btn_del)
            self.ignore_list_layout.addLayout(row)

    def update_gap(self, value):
        SETTINGS['gap'] = value
        save_config(CONFIG)
        logging.info(f"창 간격 설정 변경: {value}px")

    def update_hotkey(self, config_key, pynput_key):
        HOTKEY_CONFIG[config_key]['pynput'] = pynput_key
        # 디스플레이 텍스트 업데이트 (⌃⌥⌘ 등 기호로 변환)
        display_text = pynput_key.replace('<ctrl>', '⌃').replace('<alt>', '⌥').replace('<shift>', '⇧').replace('<cmd>', '⌘').replace('+', '')
        HOTKEY_CONFIG[config_key]['display'] = display_text
        save_config(CONFIG)
        logging.info(f"단축키 변경 [{config_key}]: {pynput_key}")
        
        # 리스너 재시작
        self.restart_hotkey_listener()

    def restart_hotkey_listener(self):
        if hasattr(self, 'ht') and self.ht.isRunning():
            self.ht.terminate()
            self.ht.wait()
        self.ht = HotkeyListenerThread()
        self.ht.start()
        logging.info("단축키 리스너 재시작 완료")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
