import sys
import socket
import logging
import os
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
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "winresizer.log"), encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 설정 및 상태 관리
CONFIG = load_config()
HOTKEY_CONFIG = CONFIG['shortcuts']
SETTINGS = CONFIG['settings']
WINDOW_HISTORY = {}

def is_nearly_equal(b1, b2, tol=10):
    if not b1 or not b2:
        return False
    return all(abs(a - b) <= tol for a, b in zip(b1, b2))

def find_monitor(bounds, monitors):
    if not bounds or not monitors:
        return 0
    cx, cy = bounds[0] + bounds[2] // 2, bounds[1] + bounds[3] // 2
    logging.info(f"[모니터 찾기] 창 중심점: ({cx}, {cy})")
    for i, m in enumerate(monitors):
        if m['x'] <= cx < m['x'] + m['width'] and m['y'] <= cy < m['y'] + m['height']:
            logging.info(f"[모니터 찾기] 일치하는 모니터 인덱스: {i}")
            return i
    logging.warning("[모니터 찾기] 일치하는 모니터를 찾지 못해 기본값(0)을 사용합니다.")
    return 0

def apply_gap(x, y, w, h, gap):
    return (x + gap, y + gap, w - 2 * gap, h - 2 * gap)

def execute_window_command(mode):
    try:
        logging.info(f"--- [명령 시작: {mode}] ---")
        
        # 1. 활성 앱 확인
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if not active_app:
            logging.warning("활성 애플리케이션을 찾을 수 없습니다.")
            return
            
        app_name = active_app.localizedName()
        if app_name in SETTINGS.get('ignore_apps', []):
            logging.info(f"[무시] {app_name} 앱은 제외 대상입니다.")
            return
            
        # 2. 모니터 정보 및 활성 창 가져오기
        monitors = get_all_monitors_info()
        target_window = get_active_window_object()
        
        if not target_window:
            logging.error(f"활성 창 객체를 가져오지 못했습니다. 앱: {app_name}")
            return
            
        current_bounds = get_window_bounds(target_window)
        if not current_bounds:
            logging.error("현재 창의 좌표를 읽어오지 못했습니다.")
            return

        logging.info(f"대상 앱: {app_name}, 현재 좌표: {current_bounds}")
        win_id = hash(target_window)
        gap = SETTINGS.get('gap', 0)

        # 3. 복구 및 디스플레이 이동 처리
        if mode == "복구":
            if win_id in WINDOW_HISTORY:
                set_window_bounds(target_window, *WINDOW_HISTORY[win_id])
                del WINDOW_HISTORY[win_id]
                logging.info("창 위치 복구 완료")
            return
        
        if mode in ["다음_디스플레이", "이전_디스플레이"]:
            idx = find_monitor(current_bounds, monitors)
            n_idx = (idx + 1 if mode == "다음_디스플레이" else idx - 1) % len(monitors)
            if idx != n_idx:
                m, nm = monitors[idx], monitors[n_idx]
                new_x = nm['x'] + (current_bounds[0] - m['x'])
                new_y = nm['y'] + (current_bounds[1] - m['y'])
                set_window_bounds(target_window, new_x, new_y, min(current_bounds[2], nm['width']), min(current_bounds[3], nm['height']))
                logging.info(f"디스플레이 이동: {idx} -> {n_idx}")
            return

        # 4. 일반 조절 전 원래 위치 저장
        if win_id not in WINDOW_HISTORY:
            WINDOW_HISTORY[win_id] = current_bounds

        idx = find_monitor(current_bounds, monitors)
        m = monitors[idx]
        screen_size = (m['width'], m['height'])
        
        # 상대 좌표 계산 (해당 모니터 내부에서의 위치)
        local_bounds = (current_bounds[0] - m['x'], current_bounds[1] - m['y'], current_bounds[2], current_bounds[3])
        
        c_size = SETTINGS.get('center_size', {'width': 1200, 'height': 800})
        
        def get_gap_pos(mode_name):
            res = calculate_window_position(screen_size, mode_name)
            if mode_name == "중앙_고정":
                res = ((screen_size[0] - c_size['width']) // 2, (screen_size[1] - c_size['height']) // 2, c_size['width'], c_size['height'])
            return apply_gap(*res, gap)

        # 스마트 순환 로직
        next_mode = mode
        if mode == "좌측_절반":
            if is_nearly_equal(local_bounds, get_gap_pos("좌측_절반")):
                next_mode = "좌측_1/3"
            elif is_nearly_equal(local_bounds, get_gap_pos("좌측_1/3")):
                next_mode = "좌측_2/3"
        elif mode == "우측_절반":
            if is_nearly_equal(local_bounds, get_gap_pos("우측_절반")):
                next_mode = "우측_1/3"
            elif is_nearly_equal(local_bounds, get_gap_pos("우측_1/3")):
                next_mode = "우측_2/3"

        # 5. 최종 좌표 계산 및 적용
        res_coords = calculate_window_position(screen_size, next_mode)
        if next_mode == "중앙_고정":
            res_coords = ((screen_size[0] - c_size['width']) // 2, (screen_size[1] - c_size['height']) // 2, c_size['width'], c_size['height'])
        
        x_rel, y_rel, w, h = apply_gap(*res_coords, gap)
        final_x, final_y = x_rel + m['x'], y_rel + m['y']
        
        logging.info(f"계산된 좌표: ({final_x}, {final_y}, {w}, {h}) [모드: {next_mode}]")
        
        success = set_window_bounds(target_window, final_x, final_y, w, h)
        if success:
            logging.info(f"창 크기 조정 성공: {next_mode}")
        else:
            logging.error("set_window_bounds API 호출 실패")
            
    except Exception as e:
        logging.error(f"명령 실행 중 예외 발생: {e}", exc_info=True)

class CommandServerThread(QThread):
    commandReceived = pyqtSignal(str)
    
    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(('localhost', 9999))
                s.listen()
                logging.info("네트워크 명령 서버 대기 중 (Port: 9999)")
                while True:
                    conn, addr = s.accept()
                    with conn:
                        data = conn.recv(1024).decode().strip()
                        if data:
                            logging.info(f"[네트워크] 명령 수신: {data} from {addr}")
                            self.commandReceived.emit(data)
        except Exception as e:
            logging.error(f"네트워크 서버 오류: {e}")

class AppObserver(QThread):
    def run(self):
        ws = NSWorkspace.sharedWorkspace()
        self.last_app = None
        while True:
            active_app = ws.frontmostApplication()
            if active_app and active_app.localizedName() != self.last_app:
                self.last_app = active_app.localizedName()
                al = SETTINGS.get('auto_layouts', {})
                if self.last_app in al:
                    logging.info(f"[자동배치] {self.last_app} 감지 -> {al[self.last_app]}")
                    QTimer.singleShot(500, lambda m=al[self.last_app]: execute_window_command(m))
            self.msleep(1000)

class HotkeyListenerThread(QThread):
    def run(self):
        if not is_accessibility_trusted():
            logging.error("접근성 권한이 없어 단축키 리스너를 시작할 수 없습니다.")
            return
        mapping = {c['pynput']: lambda m=c['mode']: execute_window_command(m) for c in HOTKEY_CONFIG.values() if c['pynput']}
        logging.info(f"단축키 리스너 시작됨 (등록된 키: {list(mapping.keys())})")
        with keyboard.GlobalHotKeys(mapping) as h:
            h.join()

class ShortcutButton(QPushButton):
    shortcutChanged = pyqtSignal(str, str)
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.is_recording = False
        self.setCheckable(True)
        self.update_style()
    def update_style(self):
        c, bg = ("#ffffff", "#5a565a") if self.is_recording else ("#ffffff" if self.text() != "단축키 입력" else "#aaaaaa", "transparent")
        self.setStyleSheet(f"QPushButton {{ background-color: {bg}; border: none; color: {c}; font-size: 13px; text-align: center; padding: 4px; border-radius: 4px; }}")
    def mousePressEvent(self, e):
        self.is_recording = True
        self.setText("입력...")
        self.update_style()
        self.setFocus()
    def keyPressEvent(self, e):
        if not self.is_recording: return
        k, m = e.key(), e.modifiers()
        if k in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]: return
        p, d = [], []
        if m & Qt.ControlModifier: p.append('<ctrl>'); d.append('⌃')
        if m & Qt.AltModifier: p.append('<alt>'); d.append('⌥')
        if m & Qt.ShiftModifier: p.append('<shift>'); d.append('⇧')
        if m & Qt.MetaModifier: p.append('<cmd>'); d.append('⌘')
        km = {Qt.Key_Left:('<left>','←'), Qt.Key_Right:('<right>','→'), Qt.Key_Up:('<up>','↑'), Qt.Key_Down:('<down>','↓'), Qt.Key_Space:('<space>','Space'), Qt.Key_Return:('<enter>','↩')}
        pk, dk = km[k] if k in km else (chr(k).lower(), chr(k).upper())
        p.append(pk); d.append(dk); self.is_recording = False; self.setText("".join(d)); self.update_style(); self.clearFocus(); self.shortcutChanged.emit("".join(d), "+".join(p))

class ShortcutRow(QFrame):
    def __init__(self, label, key, parent=None):
        super().__init__(parent); self.key = key; self.setFixedHeight(36); layout = QHBoxLayout(self); layout.setContentsMargins(40, 0, 40, 0)
        self.lbl = QLabel(label); self.lbl.setFixedWidth(100); self.lbl.setStyleSheet("color: white; font-size: 13px;")
        self.btn_f = QFrame(); self.btn_f.setStyleSheet("background-color: #4a464a; border-radius: 6px;"); bl = QHBoxLayout(self.btn_f)
        c = HOTKEY_CONFIG.get(key, {'display': '단축키 입력'})
        self.btn = ShortcutButton(c['display']); self.btn.shortcutChanged.connect(self.on_change); bl.addWidget(self.btn, 1)
        self.x = QPushButton("✕"); self.x.setFixedSize(16,16); self.x.setStyleSheet("background-color: transparent; color: #999999;"); self.x.clicked.connect(self.clear); bl.addWidget(self.x)
        layout.addWidget(self.lbl); layout.addWidget(self.btn_f, 1)
    def on_change(self, d, p):
        HOTKEY_CONFIG[self.key].update({'display': d, 'pynput': p})
        save_config(CONFIG)
        logging.info(f"[설정변경] {self.key}: {d} ({p})")
    def clear(self):
        self.btn.setText("단축키 입력")
        self.btn.update_style()
        HOTKEY_CONFIG[self.key].update({'display': '', 'pynput': ''})
        save_config(CONFIG)

class WinResizerPreferences(QWidget):
    def __init__(self):
        super().__init__()
        # 스레드 초기화 및 시작
        self.ht = HotkeyListenerThread(); self.ht.start()
        self.ao = AppObserver(); self.ao.start()
        self.cs = CommandServerThread()
        self.cs.commandReceived.connect(execute_window_command) # 메인 스레드 연결
        self.cs.start()
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("WinResizer Preferences"); self.setFixedSize(480, 800); self.setStyleSheet("background-color: #3a363a;")
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); sa = QScrollArea(); sa.setWidgetResizable(True); sa.setStyleSheet("border:none;background:#3a363a")
        sc = QWidget(); sc.setStyleSheet("background:#3a363a"); self.cl = QVBoxLayout(sc); self.cl.setContentsMargins(0, 20, 0, 20)
        
        title_sh = QLabel(" 단축키 설정"); title_sh.setStyleSheet("color: #777; font-weight: bold; font-size: 11px;"); self.cl.addWidget(title_sh)
        for k in HOTKEY_CONFIG.keys(): self.cl.addWidget(ShortcutRow(k, k))
        
        self.cl.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        title_gen = QLabel(" 일반 설정"); title_gen.setStyleSheet("color: #777; font-weight: bold; font-size: 11px;"); self.cl.addWidget(title_gen)
        
        # 간격 설정
        gap_row = QHBoxLayout(); gap_row.setContentsMargins(40, 5, 40, 5)
        gap_row.addWidget(QLabel("윈도우 간격(px)", styleSheet="color:white;font-size:13px"))
        self.gap_spin = QSpinBox(range=0, value=SETTINGS.get('gap', 5), styleSheet="color:white;background:#4a464a;border-radius:4px;padding:2px;")
        self.gap_spin.valueChanged.connect(self.save_settings); gap_row.addWidget(self.gap_spin)
        self.cl.addLayout(gap_row)
        
        # 기타 설정들... (간략화)
        self.cl.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        sa.setWidget(sc); v.addWidget(sa)

    def save_settings(self):
        SETTINGS['gap'] = self.gap_spin.value()
        save_config(CONFIG)
        logging.info("[설정] 일반 설정 저장됨")

    def closeEvent(self, event):
        logging.info("GUI 애플리케이션 종료")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Helvetica Neue", 13))
    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
