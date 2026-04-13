import sys, socket
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

CONFIG = load_config(); HOTKEY_CONFIG = CONFIG['shortcuts']; SETTINGS = CONFIG['settings']
WINDOW_HISTORY = {}

def is_nearly_equal(b1, b2, tol=8):
    return all(abs(a - b) <= tol for a, b in zip(b1, b2)) if b1 and b2 else False

def find_monitor(bounds, monitors):
    if not bounds or not monitors: return 0
    cx, cy = bounds[0]+bounds[2]//2, bounds[1]+bounds[3]//2
    for i, m in enumerate(monitors):
        if m['x'] <= cx < m['x']+m['width'] and m['y'] <= cy < m['y']+m['height']: return i
    return 0

def apply_gap(x, y, w, h, gap):
    return (x+gap, y+gap, w-2*gap, h-2*gap)

def execute_window_command(mode):
    # 제외 앱(Ignore List) 확인
    active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
    if active_app and active_app.localizedName() in SETTINGS.get('ignore_apps', []): return
    
    monitors = get_all_monitors_info(); if not monitors: return
    target_window = get_active_window_object(); if not target_window: return
    current_bounds = get_window_bounds(target_window); if not current_bounds: return
    
    win_id, gap = hash(target_window), SETTINGS.get('gap', 0)
    if mode == "복구":
        if win_id in WINDOW_HISTORY: set_window_bounds(target_window, *WINDOW_HISTORY[win_id]); del WINDOW_HISTORY[win_id]
        return
    
    # 디스플레이 이동
    if mode in ["다음_디스플레이", "이전_디스플레이"]:
        idx = find_monitor(current_bounds, monitors); n_idx = (idx+1 if mode == "다음_디스플레이" else idx-1) % len(monitors)
        if idx != n_idx:
            m, nm = monitors[idx], monitors[n_idx]; set_window_bounds(target_window, nm['x']+(current_bounds[0]-m['x']), nm['y']+(current_bounds[1]-m['y']), min(current_bounds[2], nm['width']), min(current_bounds[3], nm['height']))
        return

    if win_id not in WINDOW_HISTORY: WINDOW_HISTORY[win_id] = current_bounds
    idx = find_monitor(current_bounds, monitors); m = monitors[idx]; screen_size = (m['width'], m['height'])
    local_bounds = (current_bounds[0]-m['x'], current_bounds[1]-m['y'], current_bounds[2], current_bounds[3])
    
    # 1200x800 중앙 고정 커스텀 크기 반영 (coordinate_calculator에 전달하거나 여기서 처리)
    c_size = SETTINGS.get('center_size', {'width': 1200, 'height': 800})
    
    def get_gap_pos(mode_name):
        res = calculate_window_position(screen_size, mode_name)
        if mode_name == "중앙_고정": # 설정값 반영
            res = ((screen_size[0]-c_size['width'])//2, (screen_size[1]-c_size['height'])//2, c_size['width'], c_size['height'])
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
        res_coords = ((screen_size[0]-c_size['width'])//2, (screen_size[1]-c_size['height'])//2, c_size['width'], c_size['height'])
    
    x, y, w, h = apply_gap(*res_coords, gap)
    set_window_bounds(target_window, x + m['x'], y + m['y'], w, h)

class CommandServerThread(QThread):
    def run(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('localhost', 9999)); s.listen()
                while True:
                    conn, _ = s.accept()
                    with conn:
                        data = conn.recv(1024).decode().strip()
                        if data: QTimer.singleShot(0, lambda m=data: execute_window_command(m))
        except: pass

class AppObserver(QThread):
    def run(self):
        ws = NSWorkspace.sharedWorkspace()
        self.last_app = None
        while True:
            active_app = ws.frontmostApplication()
            if active_app and active_app.localizedName() != self.last_app:
                self.last_app = active_app.localizedName()
                al = SETTINGS.get('auto_layouts', {})
                if self.last_app in al: QTimer.singleShot(250, lambda m=al[self.last_app]: execute_window_command(m))
            self.msleep(500)

class HotkeyListenerThread(QThread):
    def run(self):
        if not is_accessibility_trusted(): return
        mapping = {c['pynput']: lambda m=c['mode']: execute_window_command(m) for c in HOTKEY_CONFIG.values() if c['pynput']}
        with keyboard.GlobalHotKeys(mapping) as h: h.join()

class ShortcutButton(QPushButton):
    shortcutChanged = pyqtSignal(str, str)
    def __init__(self, text, parent=None):
        super().__init__(text, parent); self.is_recording = False; self.setCheckable(True); self.update_style()
    def update_style(self):
        c, bg = ("#ffffff", "#5a565a") if self.is_recording else ("#ffffff" if self.text() != "단축키 입력" else "#aaaaaa", "transparent")
        self.setStyleSheet(f"QPushButton {{ background-color: {bg}; border: none; color: {c}; font-size: 13px; text-align: center; padding: 4px; border-radius: 4px; }}")
    def mousePressEvent(self, e): self.is_recording = True; self.setText("입력..."); self.update_style(); self.setFocus()
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
    def __init__(self, label, key, thread, parent=None):
        super().__init__(parent); self.key, self.thread = key, thread; self.setFixedHeight(36); layout = QHBoxLayout(self); layout.setContentsMargins(40, 0, 40, 0)
        self.lbl = QLabel(label); self.lbl.setFixedWidth(100); self.lbl.setStyleSheet("color: white; font-size: 13px;")
        self.btn_f = QFrame(); self.btn_f.setStyleSheet("background-color: #4a464a; border-radius: 6px;"); bl = QHBoxLayout(self.btn_f)
        c = HOTKEY_CONFIG.get(key, {'display': '단축키 입력'})
        self.btn = ShortcutButton(c['display']); self.btn.shortcutChanged.connect(self.on_change); bl.addWidget(self.btn, 1)
        self.x = QPushButton("✕"); self.x.setFixedSize(16,16); self.x.setStyleSheet("background-color: transparent; color: #999999;"); self.x.clicked.connect(self.clear); bl.addWidget(self.x)
        layout.addWidget(self.lbl); layout.addWidget(self.btn_f, 1)
    def on_change(self, d, p): HOTKEY_CONFIG[self.key].update({'display':d,'pynput':p}); save_config(CONFIG)
    def clear(self): self.btn.setText("단축키 입력"); self.btn.update_style(); HOTKEY_CONFIG[self.key].update({'display':'','pynput':''}); save_config(CONFIG)

class WinResizerPreferences(QWidget):
    def __init__(self):
        super().__init__(); self.ht = HotkeyListenerThread(); self.ht.start(); self.ao = AppObserver(); self.ao.start(); self.cs = CommandServerThread(); self.cs.start(); self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("마그넷 환경설정 (WinResizer)"); self.setFixedSize(480, 800); self.setStyleSheet("background-color: #3a363a;")
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); sa = QScrollArea(); sa.setWidgetResizable(True); sa.setStyleSheet("border:none;background:#3a363a")
        sc = QWidget(); sc.setStyleSheet("background:#3a363a"); self.cl = QVBoxLayout(sc); self.cl.setContentsMargins(0, 20, 0, 20)
        
        # 1. 단축키 섹션
        title_sh = QLabel(" 단축키 설정"); title_sh.setStyleSheet("color: #777; font-weight: bold; font-size: 11px;"); self.cl.addWidget(title_sh)
        for k in HOTKEY_CONFIG.keys(): self.cl.addWidget(ShortcutRow(k, k, self.ht))
        
        # 2. 일반 설정 섹션
        self.cl.addSpacerItem(QSpacerItem(20, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))
        title_gen = QLabel(" 일반 설정"); title_gen.setStyleSheet("color: #777; font-weight: bold; font-size: 11px;"); self.cl.addWidget(title_gen)
        
        # 윈도우 간격(Gap) 조절
        gap_row = QHBoxLayout(); gap_row.setContentsMargins(40, 5, 40, 5)
        gap_lbl = QLabel("윈도우 간격(px)"); gap_lbl.setStyleSheet("color: white; font-size: 13px;"); gap_row.addWidget(gap_lbl)
        self.gap_spin = QSpinBox(); self.gap_spin.setRange(0, 100); self.gap_spin.setValue(SETTINGS.get('gap', 5)); self.gap_spin.setStyleSheet("color: white; background: #4a464a; border-radius: 4px; padding: 2px;")
        self.gap_spin.valueChanged.connect(self.save_settings); gap_row.addWidget(self.gap_spin)
        self.cl.addLayout(gap_row)
        
        # 중앙 고정 크기
        cs_row = QHBoxLayout(); cs_row.setContentsMargins(40, 5, 40, 5)
        cs_lbl = QLabel("중앙 고정 가로/세로"); cs_lbl.setStyleSheet("color: white; font-size: 13px;"); cs_row.addWidget(cs_lbl)
        self.cw_spin = QSpinBox(); self.cw_spin.setRange(400, 3000); self.cw_spin.setValue(SETTINGS.get('center_size', {}).get('width', 1200)); self.cw_spin.setStyleSheet("color: white; background: #4a464a; border-radius: 4px;")
        self.ch_spin = QSpinBox(); self.ch_spin.setRange(300, 2000); self.ch_spin.setValue(SETTINGS.get('center_size', {}).get('height', 800)); self.ch_spin.setStyleSheet("color: white; background: #4a464a; border-radius: 4px;")
        self.cw_spin.valueChanged.connect(self.save_settings); self.ch_spin.valueChanged.connect(self.save_settings)
        cs_row.addWidget(self.cw_spin); cs_row.addWidget(self.ch_spin)
        self.cl.addLayout(cs_row)

        # 제외 앱 리스트
        ign_row = QVBoxLayout(); ign_row.setContentsMargins(40, 10, 40, 10)
        ign_lbl = QLabel("제외 앱 목록 (콤마로 구분)"); ign_lbl.setStyleSheet("color: white; font-size: 13px;"); ign_row.addWidget(ign_lbl)
        self.ign_edit = QLineEdit(); self.ign_edit.setText(", ".join(SETTINGS.get('ignore_apps', []))); self.ign_edit.setStyleSheet("color: white; background: #4a464a; border-radius: 4px; padding: 5px;")
        self.ign_edit.editingFinished.connect(self.save_settings); ign_row.addWidget(self.ign_edit)
        self.cl.addLayout(ign_row)

        # 로그인 시 론칭
        chk_row = QHBoxLayout(); chk_row.setContentsMargins(40, 5, 40, 5)
        self.chk_login = QCheckBox("로그인 시 론칭"); self.chk_login.setChecked(SETTINGS.get('login_launch', True)); self.chk_login.setStyleSheet("color: white; font-size: 13px;")
        self.chk_login.stateChanged.connect(self.save_settings); chk_row.addWidget(self.chk_login)
        self.cl.addLayout(chk_row)

        self.cl.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        sa.setWidget(sc); v.addWidget(sa)

    def save_settings(self):
        SETTINGS['gap'] = self.gap_spin.value()
        SETTINGS['login_launch'] = self.chk_login.isChecked()
        SETTINGS['center_size'] = {'width': self.cw_spin.value(), 'height': self.ch_spin.value()}
        SETTINGS['ignore_apps'] = [x.strip() for x in self.ign_edit.text().split(",") if x.strip()]
        save_config(CONFIG); print("[설정] 변경사항 저장됨")

    def closeEvent(self, event): event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(QFont("Helvetica Neue", 13)); window = WinResizerPreferences(); window.show(); sys.exit(app.exec_())
