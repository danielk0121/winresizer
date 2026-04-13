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
from app.src.window_manager import get_active_window_object, set_window_bounds, is_accessibility_trusted

# 기본 단축키 매핑 (수정 가능하도록 전역 변수로 관리)
HOTKEY_CONFIG = {
    '왼쪽': {'pynput': '<alt>+<cmd>+<left>', 'display': '⌥⌘←', 'mode': '좌측_절반'},
    '오른쪽': {'pynput': '<alt>+<cmd>+<right>', 'display': '⌥⌘→', 'mode': '우측_절반'},
    '위': {'pynput': '<alt>+<cmd>+<up>', 'display': '⌥⌘↑', 'mode': '위쪽_절반'},
    '아래': {'pynput': '<alt>+<cmd>+<down>', 'display': '⌥⌘↓', 'mode': '아래쪽_절반'},
    '좌측 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '좌측_1/3'},
    '중앙 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '중앙_1/3'},
    '우측 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '우측_1/3'},
    '좌측 2/3': {'pynput': '', 'display': '단축키 입력', 'mode': '좌측_2/3'},
    '우측 2/3': {'pynput': '', 'display': '단축키 입력', 'mode': '우측_2/3'},
    '중앙': {'pynput': '<alt>+<cmd>+c', 'display': '⌥⌘C', 'mode': '중앙_고정'},
    '최대화': {'pynput': '', 'display': '단축키 입력', 'mode': '최대화'},
}

def execute_window_command(mode):
    """실제 창 조절 로직 실행"""
    monitors = get_all_monitors_info()
    if not monitors: return
    
    main_monitor = monitors[0] 
    screen_size = (main_monitor['width'], main_monitor['height'])
    
    x, y, width, height = calculate_window_position(screen_size, mode)
    x += main_monitor['x']
    y += main_monitor['y']

    target_window = get_active_window_object()
    if target_window:
        set_window_bounds(target_window, x, y, width, height)
        print(f"[{mode}] 창 크기 조정 완료")

class HotkeyListenerThread(QThread):
    """단축키 리스너를 관리하는 스레드"""
    def __init__(self):
        super().__init__()
        self.listener = None

    def run(self):
        self.restart_listener()

    def restart_listener(self):
        if self.listener:
            self.listener.stop()
        
        if not is_accessibility_trusted():
            return

        mapping = {
            conf['pynput']: lambda m=conf['mode']: execute_window_command(m)
            for conf in HOTKEY_CONFIG.values() if conf['pynput']
        }

        if mapping:
            self.listener = keyboard.GlobalHotKeys(mapping)
            self.listener.start()
            print("단축키 리스너가 갱신되었습니다.")

    def stop(self):
        if self.listener:
            self.listener.stop()
        self.terminate()

class ShortcutButton(QPushButton):
    """단축키 입력을 캡처하는 특수 버튼"""
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
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                border: none;
                color: {color};
                font-size: 13px;
                text-align: center;
                padding: 4px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: #5a565a; }}
        """)

    def mousePressEvent(self, event):
        if not self.is_recording:
            self.is_recording = True
            self.setText("단축키 입력...")
            self.update_style()
            self.setFocus()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if not self.is_recording:
            return

        key = event.key()
        modifiers = event.modifiers()

        if key in [Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta]:
            return

        parts_pynput = []
        parts_display = []

        if modifiers & Qt.ControlModifier:
            parts_pynput.append('<ctrl>')
            parts_display.append('⌃')
        if modifiers & Qt.AltModifier:
            parts_pynput.append('<alt>')
            parts_display.append('⌥')
        if modifiers & Qt.ShiftModifier:
            parts_pynput.append('<shift>')
            parts_display.append('⇧')
        if modifiers & Qt.MetaModifier:
            parts_pynput.append('<cmd>')
            parts_display.append('⌘')

        key_map = {
            Qt.Key_Left: ('<left>', '←'),
            Qt.Key_Right: ('<right>', '→'),
            Qt.Key_Up: ('<up>', '↑'),
            Qt.Key_Down: ('<down>', '↓'),
            Qt.Key_Space: ('<space>', 'Space'),
            Qt.Key_Return: ('<enter>', '↩'),
        }

        if key in key_map:
            p_key, d_key = key_map[key]
        else:
            try:
                p_key = chr(key).lower()
                d_key = chr(key).upper()
            except:
                return

        parts_pynput.append(p_key)
        parts_display.append(d_key)

        pynput_str = "+".join(parts_pynput)
        display_str = "".join(parts_display)

        self.is_recording = False
        self.setText(display_str)
        self.update_style()
        self.clearFocus()
        
        self.shortcutChanged.emit(display_str, pynput_str)

class ShortcutRow(QFrame):
    def __init__(self, label_text, config_key, listener_thread, parent=None):
        super().__init__(parent)
        self.config_key = config_key
        self.listener_thread = listener_thread
        self.setFixedHeight(36)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(10)

        self.lbl_name = QLabel(label_text)
        self.lbl_name.setFixedWidth(80)
        self.lbl_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_name.setStyleSheet("color: white; font-size: 13px;")

        self.icon_placeholder = QLabel()
        self.icon_placeholder.setFixedSize(24, 14)
        self.icon_placeholder.setStyleSheet("background-color: #777777; border-radius: 2px;")

        self.btn_frame = QFrame()
        self.btn_frame.setStyleSheet("background-color: #4a464a; border-radius: 6px; border: 1px solid #5a565a;")
        btn_layout = QHBoxLayout(self.btn_frame)
        btn_layout.setContentsMargins(10, 0, 10, 0)

        conf = HOTKEY_CONFIG.get(config_key, {'display': '단축키 입력'})
        self.btn_shortcut = ShortcutButton(conf['display'])
        self.btn_shortcut.shortcutChanged.connect(self.on_shortcut_changed)
        
        btn_layout.addWidget(self.btn_shortcut, 1)

        self.btn_clear = QPushButton("✕")
        self.btn_clear.setFixedSize(16, 16)
        self.btn_clear.setCursor(Qt.PointingHandCursor)
        self.btn_clear.setStyleSheet("background-color: transparent; border: none; color: #999999;")
        self.btn_clear.clicked.connect(self.clear_shortcut)
        btn_layout.addWidget(self.btn_clear)

        layout.addWidget(self.lbl_name)
        layout.addWidget(self.icon_placeholder)
        layout.addWidget(self.btn_frame, 1)

    def on_shortcut_changed(self, display_text, pynput_text):
        HOTKEY_CONFIG[self.config_key]['display'] = display_text
        HOTKEY_CONFIG[self.config_key]['pynput'] = pynput_text
        self.listener_thread.restart_listener()

    def clear_shortcut(self):
        self.btn_shortcut.setText("단축키 입력")
        self.btn_shortcut.update_style()
        HOTKEY_CONFIG[self.config_key]['display'] = ""
        HOTKEY_CONFIG[self.config_key]['pynput'] = ""
        self.listener_thread.restart_listener()

class WinResizerPreferences(QWidget):
    def __init__(self):
        super().__init__()
        self.listener_thread = HotkeyListenerThread()
        self.listener_thread.start()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("마그넷 환경설정")
        self.setFixedSize(450, 750) # 항목이 늘어나 세로 크기 조정
        self.setStyleSheet("background-color: #3a363a;")

        main_vbox = QVBoxLayout(self)
        main_vbox.setContentsMargins(0, 0, 0, 0)

        # 스크롤 영역 추가 (항목이 많을 경우 대비)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: #3a363a; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: #3a363a;")
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(0, 20, 0, 20)
        self.content_layout.setSpacing(8)

        for label in HOTKEY_CONFIG.keys():
            row = ShortcutRow(label, label, self.listener_thread)
            self.content_layout.addWidget(row)

        self.content_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.add_checkboxes(self.content_layout)
        
        scroll.setWidget(scroll_content)
        main_vbox.addWidget(scroll)

    def add_checkboxes(self, layout):
        checkbox_frame = QFrame()
        chk_layout = QVBoxLayout(checkbox_frame)
        chk_layout.setContentsMargins(110, 0, 40, 20)
        chk_layout.setSpacing(10)
        
        chk_login = QCheckBox("로그인 시 론칭")
        chk_login.setChecked(True)
        chk_login.setStyleSheet("color: white; font-size: 13px;")
        chk_layout.addWidget(chk_login)

        layout.addWidget(checkbox_frame)

    def closeEvent(self, event):
        self.listener_thread.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Helvetica Neue", 13))
    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
