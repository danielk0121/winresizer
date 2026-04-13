import sys
import os
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt
import importlib

# app/src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import gui

class TestHotkeySwapBug(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        # 테스트를 위해 gui 모듈을 최신 상태로 로드
        importlib.reload(gui)
        self.window = gui.WinResizerPreferences()

    def test_ctrl_and_cmd_recognition_macos_fixed(self):
        """macOS에서 Qt의 Ctrl/Cmd 반전 현상을 보정한 결과가 올바른지 검증"""
        target_btn = self.window.hotkey_buttons['왼쪽']
        
        # 1. Qt.ControlModifier 입력 (macOS Qt 버그 시 실제론 Cmd로 보고됨)
        # 우리 앱은 이를 보정하여 <cmd>로 표시해야 함
        QTest.mouseClick(target_btn, Qt.LeftButton)
        QTest.keyClick(target_btn, Qt.Key_K, Qt.ControlModifier)
        
        actual_text = target_btn.text().lower()
        print(f"[보정 검증 1] Qt.ControlModifier 입력 결과: {actual_text}")
        self.assertIn("cmd", actual_text, "보정 로직에 의해 Qt.ControlModifier는 <cmd>가 되어야 합니다.")

        # 2. Qt.MetaModifier 입력 (macOS Qt 버그 시 실제론 Ctrl로 보고됨)
        # 우리 앱은 이를 보정하여 <ctrl>로 표시해야 함
        QTest.mouseClick(target_btn, Qt.LeftButton)
        QTest.keyClick(target_btn, Qt.Key_L, Qt.MetaModifier)
        
        actual_text = target_btn.text().lower()
        print(f"[보정 검증 2] Qt.MetaModifier 입력 결과: {actual_text}")
        self.assertIn("ctrl", actual_text, "보정 로직에 의해 Qt.MetaModifier는 <ctrl>가 되어야 합니다.")

if __name__ == "__main__":
    unittest.main()
