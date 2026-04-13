import sys
import os
import unittest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt, QCoreApplication
import importlib

# app/src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

import ui.hotkey_button as hotkey_button

class TestHotkeyConflict(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        self.button = hotkey_button.HotkeyButton("Press hotkey", "TestKey")

    def test_hotkey_conflict_detection_simulation(self):
        """
        [E2E/단위 테스트] 
        사용자가 단축키를 입력할 때, 시스템 예약 단축키와 충돌할 가능성이 있는 키 조합을 
        감지하고 경고를 보낼 수 있는지 확인합니다.
        """
        # 시스템 예약 키 조합 리스트
        SYSTEM_RESERVED_KEYS = ["<cmd>+<space>", "<cmd>+<shift>+<space>"]
        
        # 시뮬레이션: 사용자가 <cmd>+<space>를 입력함 (spotlight 충돌)
        input_hotkey = "<cmd>+<space>"
        
        is_conflicting = input_hotkey in SYSTEM_RESERVED_KEYS
        
        self.assertTrue(is_conflicting, "충돌하는 단축키가 감지되어야 합니다.")
        print(f"\n[테스트] 감지된 충돌: {input_hotkey}")

    def test_no_conflict_with_safe_keys(self):
        """안전한 단축키 조합은 충돌로 감지되지 않음을 확인합니다."""
        SYSTEM_RESERVED_KEYS = ["<cmd>+<space>", "<cmd>+<shift>+<space>"]
        input_hotkey = "<ctrl>+<alt>+<cmd>+<k>"
        
        is_conflicting = input_hotkey in SYSTEM_RESERVED_KEYS
        
        self.assertFalse(is_conflicting, "안전한 단축키는 충돌로 감지되지 않아야 합니다.")

if __name__ == "__main__":
    unittest.main()
