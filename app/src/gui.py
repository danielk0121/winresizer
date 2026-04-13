import sys
import threading
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# 기존 main.py의 로직 임포트
from pynput import keyboard
from app.src.coordinate_calculator import calculate_window_position
from app.src.monitor_info import get_all_monitors_info
from app.src.window_manager import get_active_window_object, set_window_bounds, is_accessibility_trusted

# 단축키 매핑 (main.py와 동일하게 유지)
HOTKEY_MAPPING = {
    '<alt>+<cmd>+<left>': '좌측_절반',
    '<alt>+<cmd>+<right>': '우측_절반',
    '<alt>+<cmd>+c': '중앙_고정'
}

def execute_window_command(mode):
    """실제 창 조절 로직 실행"""
    monitors = get_all_monitors_info()
    if not monitors: return
    
    main_monitor = monitors[0] # 첫 번째 모니터 기준 (임시)
    screen_size = (main_monitor['width'], main_monitor['height'])
    
    x, y, width, height = calculate_window_position(screen_size, mode)
    x += main_monitor['x']
    y += main_monitor['y']

    target_window = get_active_window_object()
    if target_window:
        set_window_bounds(target_window, x, y, width, height)
        print(f"[{mode}] 창 크기 조정 완료")

class HotkeyListenerThread(QThread):
    """GUI를 방해하지 않고 백그라운드에서 단축키를 감지하는 스레드"""
    def run(self):
        if not is_accessibility_trusted():
            print("오류: 접근성 권한이 없습니다. 창 조절 기능이 작동하지 않습니다.")
            return

        with keyboard.GlobalHotKeys({
            key: lambda m=mode: execute_window_command(m) for key, mode in HOTKEY_MAPPING.items()
        }) as h:
            print("백그라운드 단축키 리스너 시작됨...")
            h.join()

class ShortcutRow(QFrame):
    def __init__(self, label_text, shortcut_text, parent=None):
        super().__init__(parent)
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
        self.btn_frame.setStyleSheet("""
            QFrame {
                background-color: #4a464a;
                border-radius: 6px;
                border: 1px solid #5a565a;
            }
        """)
        btn_layout = QHBoxLayout(self.btn_frame)
        btn_layout.setContentsMargins(10, 0, 10, 0)
        btn_layout.setSpacing(5)

        self.btn_shortcut = QPushButton(shortcut_text)
        self.btn_shortcut.setCursor(Qt.PointingHandCursor)
        color = "#aaaaaa" if "입력" in shortcut_text else "white"
        self.btn_shortcut.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {color};
                font-size: 13px;
                text-align: center;
            }}
            QPushButton:hover {{
                color: white;
            }}
        """)

        btn_layout.addWidget(self.btn_shortcut, 1)

        if "입력" not in shortcut_text:
            self.btn_clear = QPushButton("✕")
            self.btn_clear.setFixedSize(16, 16)
            self.btn_clear.setCursor(Qt.PointingHandCursor)
            self.btn_clear.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    color: #999999;
                    font-size: 12px;
                }
                QPushButton:hover {
                    color: white;
                }
            """)
            btn_layout.addWidget(self.btn_clear)

        layout.addWidget(self.lbl_name)
        layout.addWidget(self.icon_placeholder)
        layout.addWidget(self.btn_frame, 1)

class WinResizerPreferences(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.start_hotkey_listener()

    def init_ui(self):
        self.setWindowTitle("마그넷 환경설정")
        self.setFixedSize(450, 650)
        self.setStyleSheet("background-color: #3a363a;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 20, 0, 20)
        main_layout.setSpacing(8)

        shortcuts = [
            ("왼쪽", "⌥⌘←"),
            ("오른쪽", "⌥⌘→"),
            ("위", "⌥⌘↑"),
            ("아래", "⌥⌘↓"),
            ("좌측 세번째", "⌥⇧⌘←"),
            ("중앙", "단축키 입력"),
            ("최대화", "단축키 입력")
        ]

        for label, shortcut in shortcuts:
            row = ShortcutRow(label, shortcut)
            main_layout.addWidget(row)

        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))
        self.add_checkboxes(main_layout)

    def add_checkboxes(self, layout):
        checkbox_frame = QFrame()
        chk_layout = QVBoxLayout(checkbox_frame)
        chk_layout.setContentsMargins(110, 0, 40, 20)
        chk_layout.setSpacing(10)

        chk_login = QCheckBox("로그인 시 론칭")
        chk_login.setChecked(True)
        chk_login.setStyleSheet("color: white; font-size: 13px;")

        chk_drag = QCheckBox("드래깅하여 윈도우 분할")
        chk_drag.setStyleSheet("color: #aaaaaa; font-size: 13px;")
        chk_drag.setEnabled(False)

        chk_layout.addWidget(chk_login)
        chk_layout.addWidget(chk_drag)

        layout.addWidget(checkbox_frame)

    def start_hotkey_listener(self):
        """백그라운드에서 단축키 리스너 실행"""
        self.hotkey_thread = HotkeyListenerThread()
        self.hotkey_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Helvetica Neue", 13)
    app.setFont(font)

    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
