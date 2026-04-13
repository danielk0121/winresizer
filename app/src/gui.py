import sys
import socket
import logging
import os
import datetime
import time
import threading
from AppKit import NSWorkspace
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QScrollArea, QSpinBox, QLineEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from pynput import keyboard
from coordinate_calculator import calculate_window_position
from monitor_info import get_all_monitors_info
from window_manager import get_active_window_object, set_window_bounds, get_window_bounds, is_accessibility_trusted
from config_manager import load_config, save_config

# 로깅 설정
LOG_DIR = "log"
if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
kst_now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = f"winresizer_{kst_now}_KST.log"
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
                    handlers=[logging.FileHandler(os.path.join(LOG_DIR, log_filename), encoding='utf-8'), logging.StreamHandler(sys.stdout)])

logging.debug("애플리케이션 시작 및 로깅 설정 완료")

CONFIG = load_config()
HOTKEY_CONFIG = CONFIG['shortcuts']
SETTINGS = CONFIG['settings']
WINDOW_HISTORY = {}
GLOBAL_RECORDING = False # 단축키 녹화 중 여부 플래그

def is_nearly_equal(b1, b2, tol=20):
    if not b1 or not b2: return False
    return all(abs(a - b) <= tol for a, b in zip(b1, b2))

def apply_gap(x, y, w, h, gap):
    return (x + gap, y + gap, w - 2 * gap, h - 2 * gap)

def execute_window_command(mode):
    try:
        logging.debug(f"명령 실행 시작: {mode}")
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if not active_app:
            logging.debug("활성 앱을 찾을 수 없음")
            return
            
        app_name = active_app.localizedName()
        if app_name in SETTINGS.get('ignore_apps', []):
            logging.debug(f"무시 대상 앱: {app_name}")
            return
            
        monitors = get_all_monitors_info()
        target_window = get_active_window_object()
        if not target_window:
            logging.debug("타겟 윈도우를 찾을 수 없음")
            return
            
        current_bounds = get_window_bounds(target_window)
        if not current_bounds:
            logging.debug("윈도우 경계를 가져올 수 없음")
            return
            
        win_id, gap = hash(target_window), SETTINGS.get('gap', 5)
        
        if mode == "복구":
            if win_id in WINDOW_HISTORY:
                set_window_bounds(target_window, *WINDOW_HISTORY[win_id])
                del WINDOW_HISTORY[win_id]
                logging.info("윈도우 복구 완료")
            return
        
        if win_id not in WINDOW_HISTORY: WINDOW_HISTORY[win_id] = current_bounds
        idx = 0
        cx, cy = current_bounds[0] + current_bounds[2] // 2, current_bounds[1] + current_bounds[3] // 2
        for i, m in enumerate(monitors):
            if m['x'] <= cx < m['x'] + m['width'] and m['y'] <= cy < m['y'] + m['height']:
                idx = i; break
        m = monitors[idx]
        screen_size = (m['width'], m['height'])
        local_bounds = (current_bounds[0] - m['x'], current_bounds[1] - m['y'], current_bounds[2], current_bounds[3])
        
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
        set_window_bounds(target_window, x_rel + m['x'], y_rel + m['y'], w, h)
        logging.info(f"명령 실행 완료: {next_mode}")
    except Exception as e: 
        logging.error(f"명령 실행 중 예외 발생: {e}", exc_info=True)

class HotkeyListenerThread(QThread):
    def run(self):
        logging.info("리스너 스레드 시작")
        if not is_accessibility_trusted():
            logging.warning("Accessibility 권한이 없어 리스너를 시작할 수 없습니다.")
            return
        
        current_keys = set()
        
        def on_press(key):
            if GLOBAL_RECORDING:
                return # 녹화 중일 때는 전역 단축키 처리 안 함
                
            try:
                k = key.char.lower() if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
                current_keys.add(k)
                
                # 매번 모든 키 입력을 HOTKEY_CONFIG와 대조
                for cfg in HOTKEY_CONFIG.values():
                    pynput_str = cfg['pynput']
                    if not pynput_str: continue
                    
                    required = set(pynput_str.replace('<', '').replace('>', '').split('+'))
                    if required.issubset(current_keys):
                        logging.debug(f"단축키 감지됨: {pynput_str}")
                        execute_window_command(cfg['mode'])
                        current_keys.clear()
                        break
            except Exception as e:
                logging.error(f"on_press 오류: {e}")

        def on_release(key):
            try:
                k = key.char.lower() if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
                if k in current_keys: current_keys.remove(k)
            except Exception as e:
                logging.error(f"on_release 오류: {e}")

        logging.info("영구 단축키 엔진 시작됨")
        try:
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            logging.error(f"리스너 실행 중 오류: {e}", exc_info=True)

class WinResizerPreferences(QWidget):
    def __init__(self):
        super().__init__()
        self.hotkey_buttons = {} # 버튼 객체 보관용
        self.ht = HotkeyListenerThread(); self.ht.start()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("WinResizer 설정"); self.setMinimumSize(450, 600); self.setStyleSheet("background-color: #2b2b2b; color: white;")
        layout = QVBoxLayout(self)
        
        # 간격 설정
        self.gap_spin = QSpinBox(); self.gap_spin.setRange(0, 50); self.gap_spin.setValue(SETTINGS.get('gap', 5))
        self.gap_spin.valueChanged.connect(lambda v: (SETTINGS.update({'gap': v}), save_config(CONFIG)))
        layout.addWidget(QLabel("창 간격 (Gap):")); layout.addWidget(self.gap_spin)

        # 단축키 목록
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll_content = QWidget(); self.scroll_layout = QVBoxLayout(scroll_content)
        for name, cfg in HOTKEY_CONFIG.items():
            row = QHBoxLayout()
            label = QLabel(name)
            label.setMinimumWidth(100)
            row.addWidget(label)
            
            btn = HotkeyButton(cfg['display'], name)
            btn.hotkeyChanged.connect(self.update_hotkey)
            self.hotkey_buttons[name] = btn
            row.addWidget(btn)
            
            # 삭제 버튼 추가
            del_btn = QPushButton("✕")
            del_btn.setFixedSize(30, 30)
            del_btn.setToolTip(f"{name} 단축키 초기화")
            del_btn.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: #bbb;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e74c3c;
                    color: white;
                }
            """)
            del_btn.clicked.connect(lambda checked, k=name: self.update_hotkey(k, ""))
            row.addWidget(del_btn)
            
            self.scroll_layout.addLayout(row)
        scroll.setWidget(scroll_content); layout.addWidget(scroll)
        
        btn_quit = QPushButton("앱 종료"); btn_quit.clicked.connect(QApplication.instance().quit); layout.addWidget(btn_quit)

    def update_hotkey(self, k, pk):
        logging.info(f"단축키 갱신 요청: {k} -> {pk}")
        HOTKEY_CONFIG[k]['pynput'] = pk
        if pk:
            # <ctrl>+<alt>+k -> ctrl + alt + k 형식으로 변환
            display_text = pk.replace('<', '').replace('>', '').replace('+', ' + ')
            HOTKEY_CONFIG[k]['display'] = display_text
        else:
            display_text = "단축키 입력"
            HOTKEY_CONFIG[k]['display'] = display_text
            
        # UI 즉시 반영
        if k in self.hotkey_buttons:
            self.hotkey_buttons[k].setText(display_text)
            
        save_config(CONFIG)
        logging.info(f"단축키 갱신 완료: {pk}")

class HotkeyButton(QPushButton):
    hotkeyChanged = pyqtSignal(str, str)
    def __init__(self, text, key):
        super().__init__(text); self.key = key; self.recording = False
        self.clicked.connect(self.start_recording)
        
    def start_recording(self):
        global GLOBAL_RECORDING
        logging.debug(f"단축키 녹화 시작: {self.key}")
        self.recording = True
        GLOBAL_RECORDING = True
        self.setText("입력 대기...")
        self.grabKeyboard()
        
    def keyPressEvent(self, event):
        if not self.recording:
            super().keyPressEvent(event)
            return
            
        if event.key() == Qt.Key_Escape:
            logging.debug("단축키 녹화 취소 (Escape)")
            self.stop_recording()
            self.setText(HOTKEY_CONFIG[self.key]['display'])
            return
            
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            logging.debug(f"단축키 삭제 요청: {self.key}")
            self.hotkeyChanged.emit(self.key, "")
            self.setText("단축키 입력")
            self.stop_recording()
            return
        
        parts, d_parts = [], []
        mods = event.modifiers()
        if mods & Qt.ControlModifier: parts.append('<ctrl>'); d_parts.append('⌃')
        if mods & Qt.AltModifier: parts.append('<alt>'); d_parts.append('⌥')
        if mods & Qt.MetaModifier: parts.append('<cmd>'); d_parts.append('⌘')
        
        k = event.key()
        kn = {Qt.Key_Left:'left', Qt.Key_Right:'right', Qt.Key_Up:'up', Qt.Key_Down:'down'}.get(k, chr(k).lower() if 32 <= k <= 126 else None)
        if kn:
            pk = "+".join(parts + ([f"<{kn}>"] if len(kn)>1 else [kn]))
            logging.debug(f"새 단축키 입력됨: {pk}")
            self.hotkeyChanged.emit(self.key, pk)
            # setText는 hotkeyChanged -> update_hotkey를 통해 처리되므로 여기서 직접 호출하지 않아도 되지만, 
            # 즉각적인 피드백을 위해 update_hotkey와 동일한 로직 적용
            display_text = pk.replace('<', '').replace('>', '').replace('+', ' + ')
            self.setText(display_text)
            self.stop_recording()

    def stop_recording(self):
        global GLOBAL_RECORDING
        logging.debug(f"단축키 녹화 종료: {self.key}")
        self.recording = False
        GLOBAL_RECORDING = False
        self.releaseKeyboard()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WinResizerPreferences(); window.show()
    sys.exit(app.exec_())
