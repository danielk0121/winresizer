import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QCheckBox, QFrame, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor

class ShortcutRow(QFrame):
    def __init__(self, label_text, shortcut_text, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(10)

        # 1. 기능 이름 (레이블)
        self.lbl_name = QLabel(label_text)
        self.lbl_name.setFixedWidth(80)
        self.lbl_name.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.lbl_name.setStyleSheet("color: white; font-size: 13px;")

        # 2. 기능 아이콘 자리 (단순 둥근 사각형)
        self.icon_placeholder = QLabel()
        self.icon_placeholder.setFixedSize(24, 14)
        self.icon_placeholder.setStyleSheet("background-color: #777777; border-radius: 2px;")

        # 3. 단축키 표시 버튼 영역 (버튼 + X 버튼)
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

        # 단축키 텍스트
        self.btn_shortcut = QPushButton(shortcut_text)
        self.btn_shortcut.setCursor(Qt.CursorShape.PointingHandCursor)
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

        # X 버튼 (삭제) - '입력' 텍스트가 아닌 경우만 활성화
        if "입력" not in shortcut_text:
            self.btn_clear = QPushButton("✕")
            self.btn_clear.setFixedSize(16, 16)
            self.btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
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

    def init_ui(self):
        self.setWindowTitle("마그넷 환경설정")
        self.setFixedSize(450, 650)
        self.setStyleSheet("background-color: #3a363a;") # 메인 배경 다크 그레이

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 20, 0, 20)
        main_layout.setSpacing(8)

        # 단축키 목록
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

        # 빈 공간 채우기
        main_layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # 하단 체크박스 옵션들
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
        chk_drag.setEnabled(False) # 비활성화 처리 예시

        chk_layout.addWidget(chk_login)
        chk_layout.addWidget(chk_drag)

        layout.addWidget(checkbox_frame)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # macOS 다크 모드 폰트 렌더링 최적화
    font = QFont("Helvetica Neue", 13)
    app.setFont(font)

    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec())
