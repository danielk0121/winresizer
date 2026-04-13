import sys
from AppKit import NSWorkspace
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy, QScrollArea
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

def is_nearly_equal(b1, b2, tol=5):
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
    # 윈도우 제외 리스트(Ignore List) 확인
    active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
    if active_app and active_app.localizedName() in SETTINGS.get('ignore_apps', []):
        print(f"[무시] {active_app.localizedName()} 앱에서는 단축키가 작동하지 않습니다.")
        return

    monitors = get_all_monitors_info(); if not monitors: return
    target_window = get_active_window_object(); if not target_window: return
    current_bounds = get_window_bounds(target_window); if not current_bounds: return
    
    win_id, gap = hash(target_window), SETTINGS.get('gap', 0)
    if mode == "복구":
        if win_id in WINDOW_HISTORY:
            set_window_bounds(target_window, *WINDOW_HISTORY[win_id]); del WINDOW_HISTORY[win_id]
        return
    if mode in ["다음_디스플레이", "이전_디스플레이"]:
        idx = find_monitor(current_bounds, monitors)
        n_idx = (idx+1 if mode == "다음_디스플레이" else idx-1) % len(monitors)
        if idx != n_idx:
            m, nm = monitors[idx], monitors[n_idx]
            set_window_bounds(target_window, nm['x']+(current_bounds[0]-m['x']), nm['y']+(current_bounds[1]-m['y']), min(current_bounds[2], nm['width']), min(current_bounds[3], nm['height']))
        return

    if win_id not in WINDOW_HISTORY: WINDOW_HISTORY[win_id] = current_bounds
    idx = find_monitor(current_bounds, monitors); m = monitors[idx]
    screen_size = (m['width'], m['height'])
    local_bounds = (current_bounds[0]-m['x'], current_bounds[1]-m['y'], current_bounds[2], current_bounds[3])
    
    next_mode = mode
    def get_gap_pos(mode_name): return apply_gap(*calculate_window_position(screen_size, mode_name), gap)
    if mode == "좌측_절반":
        if is_nearly_equal(local_bounds, get_gap_pos("좌측_절반")): next_mode = "좌측_1/3"
        elif is_nearly_equal(local_bounds, get_gap_pos("좌측_1/3")): next_mode = "좌측_2/3"
    elif mode == "우측_절반":
        if is_nearly_equal(local_bounds, get_gap_pos("우측_절반")): next_mode = "우측_1/3"
        elif is_nearly_equal(local_bounds, get_gap_pos("우측_1/3")): next_mode = "우측_2/3"

    x, y, w, h = apply_gap(*calculate_window_position(screen_size, next_mode), gap)
    set_window_bounds(target_window, x + m['x'], y + m['y'], w, h)

class AppObserver(QThread):
    def run(self):
        ws = NSWorkspace.sharedWorkspace()
        self.last_app = None
        while True:
            active_app = ws.frontmostApplication()
            if active_app and active_app.localizedName() != self.last_app:
                self.last_app = active_app.localizedName()
                auto_layouts = SETTINGS.get('auto_layouts', {})
                if self.last_app in auto_layouts:
                    QTimer.singleShot(200, lambda m=auto_layouts[self.last_app]: execute_window_command(m))
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
        self.lbl = QLabel(label); self.lbl.setFixedWidth(80); self.lbl.setStyleSheet("color: white; font-size: 13px;")
        self.btn_f = QFrame(); self.btn_f.setStyleSheet("background-color: #4a464a; border-radius: 6px;"); bl = QHBoxLayout(self.btn_f)
        c = HOTKEY_CONFIG.get(key, {'display': '단축키 입력'})
        self.btn = ShortcutButton(c['display']); self.btn.shortcutChanged.connect(self.on_change); bl.addWidget(self.btn, 1)
        self.x = QPushButton("✕"); self.x.setFixedSize(16,16); self.x.setStyleSheet("background-color: transparent; color: #999999;"); self.x.clicked.connect(self.clear); bl.addWidget(self.x)
        layout.addWidget(self.lbl); layout.addWidget(self.btn_f, 1)
    def on_change(self, d, p): HOTKEY_CONFIG[self.key].update({'display':d,'pynput':p}); save_config(CONFIG)
    def clear(self): self.btn.setText("단축키 입력"); self.btn.update_style(); HOTKEY_CONFIG[self.key].update({'display':'','pynput':''}); save_config(CONFIG)

class WinResizerPreferences(QWidget):
    def __init__(self):
        super().__init__(); self.ht = HotkeyListenerThread(); self.ht.start(); self.ao = AppObserver(); self.ao.start(); self.init_ui()
    def init_ui(self):
        self.setWindowTitle("마그넷 환경설정"); self.setFixedSize(450, 750); self.setStyleSheet("background-color: #3a363a;")
        v = QVBoxLayout(self); v.setContentsMargins(0,0,0,0); sa = QScrollArea(); sa.setWidgetResizable(True); sa.setStyleSheet("border:none;background:#3a363a")
        sc = QWidget(); sc.setStyleSheet("background:#3a363a"); self.cl = QVBoxLayout(sc); self.cl.setContentsMargins(0, 20, 0, 20)
        for k in HOTKEY_CONFIG.keys(): self.cl.addWidget(ShortcutRow(k, k, self.ht))
        self.cl.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        f = QFrame(); cl = QVBoxLayout(f); cl.setContentsMargins(110, 0, 40, 20); chk = QCheckBox("로그인 시 론칭"); chk.setChecked(SETTINGS.get('login_launch', True)); chk.setStyleSheet("color: white; font-size: 13px;")
        cl.addWidget(chk); self.cl.addWidget(f); sa.setWidget(sc); v.addWidget(sa)
    def closeEvent(self, event): event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(QFont("Helvetica Neue", 13)); window = WinResizerPreferences(); window.show(); sys.exit(app.exec_())
