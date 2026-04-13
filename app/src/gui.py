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
from window_manager import (
    get_active_window_object, set_window_bounds, get_window_bounds, 
    is_accessibility_trusted, activate_application
)
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
        
        # [수정] 창 이동 후 포커스가 유실되는 현상을 방지하기 위해 강제 재활성화
        try:
            pid = active_app.processIdentifier()
            activate_application(pid)
        except:
            pass
            
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
        
        last_trigger_time = 0

        def on_press(key):
            nonlocal last_trigger_time
            if GLOBAL_RECORDING:
                return
                
            try:
                k = key.char.lower() if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
                current_keys.add(k)
                
                now = time.time()
                for cfg in HOTKEY_CONFIG.values():
                    pynput_str = cfg['pynput']
                    if not pynput_str: continue
                    
                    required = set(pynput_str.replace('<', '').replace('>', '').split('+'))
                    if required.issubset(current_keys):
                        # 너무 빠른 연속 트리거 방지 (0.2초 쿨다운)
                        if now - last_trigger_time > 0.2:
                            logging.debug(f"단축키 감지됨: {pynput_str}")
                            execute_window_command(cfg['mode'])
                            last_trigger_time = now
                        
                        # [중요] 모든 키를 지우지 않고, 수식 키가 아닌 키만 제거하여 연속 입력 지원
                        # 혹은 수식 키를 제외한 세트만 유지
                        modifiers = {'ctrl', 'alt', 'cmd', 'shift', 'ctrl_l', 'ctrl_r', 'alt_l', 'alt_r', 'cmd_l', 'cmd_r', 'shift_l', 'shift_r'}
                        current_keys.intersection_update(modifiers)
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
        self.setWindowTitle("WinResizer 설정"); self.setMinimumSize(570, 1120); self.setStyleSheet("background-color: #2b2b2b; color: white;")
        layout = QVBoxLayout(self)
        
        # 간격 설정
        self.gap_spin = QSpinBox(); self.gap_spin.setRange(0, 50); self.gap_spin.setValue(SETTINGS.get('gap', 5))
        self.gap_spin.valueChanged.connect(lambda v: (SETTINGS.update({'gap': v}), save_config(CONFIG)))
        layout.addWidget(QLabel("창 간격 (Gap):")); layout.addWidget(self.gap_spin)

        # 단축키 목록
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame) # 테두리 제거로 더 깔끔하게
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
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
        
        # 모든 단축키 삭제 버튼 추가 (사용자 요청 사항)
        btn_clear_all = QPushButton("모든 단축키 삭제")
        btn_clear_all.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        btn_clear_all.clicked.connect(self.clear_all_shortcuts)
        layout.addWidget(btn_clear_all)
        
        btn_quit = QPushButton("앱 종료"); btn_quit.clicked.connect(QApplication.instance().quit); layout.addWidget(btn_quit)

    def clear_all_shortcuts(self):
        """모든 단축키 설정을 초기화합니다."""
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, '확인', '정말 모든 단축키를 삭제하시겠습니까?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for k in list(HOTKEY_CONFIG.keys()):
                self.update_hotkey(k, "")
            logging.info("모든 단축키가 초기화되었습니다.")

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
        import sys
        
        # macOS 등 플랫폼별 Modifier 인식 버그 수정 (사용자 보고 기반: Ctrl/Cmd 반전 현상)
        if sys.platform == 'darwin':
            # 사용자 보고: macOS에서 Ctrl을 누르면 cmd가, Cmd를 누르면 ctrl이 찍힘
            # 따라서 Qt가 반대로 보고하는 경우를 대비해 매핑을 보정함
            if mods & Qt.ControlModifier: 
                parts.append('<cmd>')
                d_parts.append('⌘')
            if mods & Qt.MetaModifier: 
                parts.append('<ctrl>')
                d_parts.append('⌃')
        else:
            # 타 플랫폼(Windows/Linux)은 표준 매핑 사용
            if mods & Qt.ControlModifier: 
                parts.append('<ctrl>')
                d_parts.append('⌃')
            if mods & Qt.MetaModifier: 
                parts.append('<cmd>')
                d_parts.append('⌘')

        # 2. Alt (Option) 키 처리 (공통)
        if mods & Qt.AltModifier: 
            parts.append('<alt>')
            d_parts.append('⌥')
        
        # 3. Shift 키 처리 (공통)
        if mods & Qt.ShiftModifier:
            parts.append('<shift>')
            d_parts.append('⇧')
        
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
