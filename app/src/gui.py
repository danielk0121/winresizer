import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QFont

from pynput import keyboard
from app.src.coordinate_calculator import calculate_window_position
from app.src.monitor_info import get_all_monitors_info
from app.src.window_manager import get_active_window_object, set_window_bounds, get_window_bounds, is_accessibility_trusted
from app.src.config_manager import load_config, save_config

# 설정 불러오기
CONFIG = load_config()
HOTKEY_CONFIG = CONFIG['shortcuts']
SETTINGS = CONFIG['settings']

def is_nearly_equal(bounds1, bounds2, tolerance=5):
    """두 좌표값이 오차 범위 내에서 일치하는지 확인 (Gap 고려)"""
    if not bounds1 or not bounds2: return False
    return all(abs(a - b) <= tolerance for a, b in zip(bounds1, bounds2))

def find_current_monitor_index(window_bounds, monitors):
    """현재 창의 중심점이 속해 있는 모니터의 인덱스를 반환"""
    if not window_bounds or not monitors: return 0
    cx = window_bounds[0] + window_bounds[2] // 2
    cy = window_bounds[1] + window_bounds[3] // 2
    for i, m in enumerate(monitors):
        if (m['x'] <= cx < m['x'] + m['width']) and \
           (m['y'] <= cy < m['y'] + m['height']):
            return i
    return 0

def apply_gap(x, y, w, h, gap):
    """창 좌표에 간격(Gap)을 적용하여 반환"""
    return (x + gap, y + gap, w - 2 * gap, h - 2 * gap)

def execute_window_command(mode):
    """실제 창 조절 로직 실행 (Gap 반영 포함)"""
    monitors = get_all_monitors_info()
    if not monitors: return
    
    target_window = get_active_window_object()
    if not target_window: return
    
    current_bounds = get_window_bounds(target_window)
    if not current_bounds: return

    gap = SETTINGS.get('gap', 0)

    # 1. 디스플레이 이동 처리
    if mode in ["다음_디스플레이", "이전_디스플레이"]:
        curr_idx = find_current_monitor_index(current_bounds, monitors)
        next_idx = (curr_idx + 1 if mode == "다음_디스플레이" else curr_idx - 1) % len(monitors)
        if curr_idx == next_idx: return
        
        curr_m, next_m = monitors[curr_idx], monitors[next_idx]
        rel_x, rel_y = current_bounds[0] - curr_m['x'], current_bounds[1] - curr_m['y']
        
        new_x, new_y = next_m['x'] + rel_x, next_m['y'] + rel_y
        new_w, new_h = min(current_bounds[2], next_m['width']), min(current_bounds[3], next_m['height'])
        
        set_window_bounds(target_window, new_x, new_y, new_w, new_h)
        return

    # 2. 일반 분할 모드 처리
    curr_idx = find_current_monitor_index(current_bounds, monitors)
    main_monitor = monitors[curr_idx]
    screen_size = (main_monitor['width'], main_monitor['height'])
    
    local_bounds = (
        current_bounds[0] - main_monitor['x'],
        current_bounds[1] - main_monitor['y'],
        current_bounds[2],
        current_bounds[3]
    )

    next_mode = mode
    # 스마트 순환 (Gap이 적용되지 않은 순수 좌표와 비교)
    def get_pure_pos(m): return calculate_window_position(screen_size, m)
    def get_gap_pos(m): return apply_gap(*get_pure_pos(m), gap)

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

    # 최종 좌표 계산 및 Gap 적용
    pure_x, pure_y, pure_w, pure_h = calculate_window_position(screen_size, next_mode)
    x, y, w, h = apply_gap(pure_x, pure_y, pure_w, pure_h, gap)
    
    x += main_monitor['x']
    y += main_monitor['y']

    set_window_bounds(target_window, x, y, w, h)
    print(f"[{next_mode}] 창 크기 조정 완료 (Gap {gap}px 적용)")

class HotkeyListenerThread(QThread):
    def __init__(self):
        super().__init__()
        self.listener = None

    def run(self):
        self.restart_listener()

    def restart_listener(self):
        if self.listener: self.listener.stop()
        if not is_accessibility_trusted(): return
        mapping = {
            conf['pynput']: lambda m=conf['mode']: execute_window_command(m)
            for conf in HOTKEY_CONFIG.values() if conf['pynput']
        }
        if mapping:
            self.listener = keyboard.GlobalHotKeys(mapping)
            self.listener.start()

    def stop(self):
        if self.listener: self.listener.stop()
        self.terminate()

class ShortcutButton(QPushButton):
    shortcutChanged = pyqtSignal(str, str)
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.is_recording = False
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.update_style()

    def update_style(self):
        color = "#ffffff" if self.text() != "단축키 입력" else "#aaaaaa"
        bg = "#5a565a" if self.is_recording else "transparent"
        self.setStyleSheet(f"QPushButton {{ background-color: {bg}; border: none; color: {color}; font-size: 13px; text-align: center; padding: 4px; border-radius: 4px; }} QPushButton:hover {{ background-color: #5a565a; }}")

    def mousePressEvent(self, event):
        if not self.is_recording:
            self.is_recording = True
            self.setText("단축키 입력...")
            self.update_style()
            self.setFocus()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if not self.is_recording: return
        key, modifiers = event.key(), event.modifiers()
        if key in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]: return
        parts_pynput, parts_display = [], []
        if modifiers & Qt.ControlModifier: parts_pynput.append('<ctrl>'); parts_display.append('⌃')
        if modifiers & Qt.AltModifier: parts_pynput.append('<alt>'); parts_display.append('⌥')
        if modifiers & Qt.ShiftModifier: parts_pynput.append('<shift>'); parts_display.append('⇧')
        if modifiers & Qt.MetaModifier: parts_pynput.append('<cmd>'); parts_display.append('⌘')
        key_map = { Qt.Key_Left: ('<left>', '←'), Qt.Key_Right: ('<right>', '→'), Qt.Key_Up: ('<up>', '↑'), Qt.Key_Down: ('<down>', '↓'), Qt.Key_Space: ('<space>', 'Space'), Qt.Key_Return: ('<enter>', '↩') }
        if key in key_map: p_key, d_key = key_map[key]
        else: p_key, d_key = chr(key).lower(), chr(key).upper()
        parts_pynput.append(p_key); parts_display.append(d_key)
        self.is_recording = False
        self.setText("".join(parts_display))
        self.update_style(); self.clearFocus()
        self.shortcutChanged.emit("".join(parts_display), "+".join(parts_pynput))

class ShortcutRow(QFrame):
    def __init__(self, label_text, config_key, listener_thread, parent=None):
        super().__init__(parent)
        self.config_key, self.listener_thread = config_key, listener_thread
        self.setFixedHeight(36)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 0, 40, 0); layout.setSpacing(10)
        self.lbl_name = QLabel(label_text)
        self.lbl_name.setFixedWidth(80); self.lbl_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter); self.lbl_name.setStyleSheet("color: white; font-size: 13px;")
        self.icon_placeholder = QLabel(); self.icon_placeholder.setFixedSize(24, 14); self.icon_placeholder.setStyleSheet("background-color: #777777; border-radius: 2px;")
        self.btn_frame = QFrame(); self.btn_frame.setStyleSheet("background-color: #4a464a; border-radius: 6px; border: 1px solid #5a565a;")
        btn_layout = QHBoxLayout(self.btn_frame); btn_layout.setContentsMargins(10, 0, 10, 0)
        conf = HOTKEY_CONFIG.get(config_key, {'display': '단축키 입력'})
        self.btn_shortcut = ShortcutButton(conf['display'])
        self.btn_shortcut.shortcutChanged.connect(self.on_shortcut_changed)
        btn_layout.addWidget(self.btn_shortcut, 1)
        self.btn_clear = QPushButton("✕"); self.btn_clear.setFixedSize(16, 16); self.btn_clear.setStyleSheet("background-color: transparent; border: none; color: #999999;")
        self.btn_clear.clicked.connect(self.clear_shortcut)
        btn_layout.addWidget(self.btn_clear)
        layout.addWidget(self.lbl_name); layout.addWidget(self.icon_placeholder); layout.addWidget(self.btn_frame, 1)

    def on_shortcut_changed(self, display_text, pynput_text):
        HOTKEY_CONFIG[self.config_key].update({'display': display_text, 'pynput': pynput_text})
        save_config(CONFIG); self.listener_thread.restart_listener()

    def clear_shortcut(self):
        self.btn_shortcut.setText("단축키 입력"); self.btn_shortcut.update_style()
        HOTKEY_CONFIG[self.config_key].update({'display': '', 'pynput': ''})
        save_config(CONFIG); self.listener_thread.restart_listener()

class WinResizerPreferences(QWidget):
    def __init__(self):
        super().__init__()
        self.listener_thread = HotkeyListenerThread(); self.listener_thread.start()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("마그넷 환경설정"); self.setFixedSize(450, 750); self.setStyleSheet("background-color: #3a363a;")
        main_vbox = QVBoxLayout(self); main_vbox.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setStyleSheet("QScrollArea { border: none; background-color: #3a363a; }")
        scroll_content = QWidget(); scroll_content.setStyleSheet("background-color: #3a363a;")
        self.content_layout = QVBoxLayout(scroll_content); self.content_layout.setContentsMargins(0, 20, 0, 20); self.content_layout.setSpacing(8)
        for label in HOTKEY_CONFIG.keys():
            self.content_layout.addWidget(ShortcutRow(label, label, self.listener_thread))
        self.content_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        checkbox_frame = QFrame(); chk_layout = QVBoxLayout(checkbox_frame); chk_layout.setContentsMargins(110, 0, 40, 20); chk_layout.setSpacing(10)
        chk_login = QCheckBox("로그인 시 론칭"); chk_login.setChecked(SETTINGS.get('login_launch', True)); chk_login.setStyleSheet("color: white; font-size: 13px;")
        chk_layout.addWidget(chk_login); self.content_layout.addWidget(checkbox_frame)
        scroll.setWidget(scroll_content); main_vbox.addWidget(scroll)

    def closeEvent(self, event): self.listener_thread.stop(); event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(QFont("Helvetica Neue", 13))
    window = WinResizerPreferences(); window.show(); sys.exit(app.exec_())
