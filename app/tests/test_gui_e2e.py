import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json
import time
import importlib
from PyQt5.QtWidgets import QApplication, QPushButton, QMessageBox
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# app/src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# config_manager는 core 하위로 이동됨
from core import config_manager

# 실제 설정 파일을 더럽히지 않기 위해 테스트용 설정 파일 경로 설정
TEST_CONFIG_FILE = os.path.join(os.path.dirname(src_dir), "config", "test_config.json")

class TestGuiE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. QApplication 인스턴스 생성
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

        # 2. CONFIG_FILE 경로 패치
        cls.config_patcher = patch('core.config_manager.CONFIG_FILE', TEST_CONFIG_FILE)
        cls.config_patcher.start()

        # 3. gui 모듈 로드
        import gui
        importlib.reload(gui)
        cls.gui = gui

        # 테스트용 기본 설정 파일 생성
        if os.path.exists(TEST_CONFIG_FILE):
            os.remove(TEST_CONFIG_FILE)

    @classmethod
    def tearDownClass(cls):
        # 테스트 완료 후 원상복구 및 임시 파일 삭제
        cls.config_patcher.stop()
        if os.path.exists(TEST_CONFIG_FILE):
            os.remove(TEST_CONFIG_FILE)

    def setUp(self):
        # 매 테스트마다 새로운 윈도우 인스턴스 생성
        self.window = self.gui.WinResizerPreferences()

    def test_hotkey_recording_and_persistence(self):
        """Verify that hotkeys are recorded and saved correctly."""
        
        # 1. Find 'Left' hotkey button
        target_btn = self.window.hotkey_button_map.get('Left')
        self.assertIsNotNone(target_btn, "Could not find 'Left' hotkey button.")
        
        # 2. Click button (start recording)
        QTest.mouseClick(target_btn, Qt.LeftButton)
        self.assertEqual(target_btn.text(), "입력 대기...")
        self.assertTrue(target_btn.is_recording)
        
        # 3. Simulate key press (Ctrl + Alt + K)
        QTest.keyClick(target_btn, Qt.Key_K, Qt.ControlModifier | Qt.AltModifier)
        
        # 4. Check GUI state
        expected_mod = "cmd" if sys.platform == 'darwin' else "ctrl"
        self.assertEqual(target_btn.text().lower(), f"{expected_mod} + alt + k")
        self.assertFalse(target_btn.is_recording)
        
        # 5. Verify file save
        time.sleep(0.5) 
        self.assertTrue(os.path.exists(TEST_CONFIG_FILE))
        
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
            
        shortcut_data = saved_config['shortcuts']['Left']
        self.assertEqual(shortcut_data['pynput'], f"<{expected_mod}>+<alt>+k")
        self.assertEqual(shortcut_data['display'].lower(), f"{expected_mod} + alt + k")

    def test_hotkey_4_keys_combination(self):
        """Verify 4-key combo (Ctrl+Alt+Shift+Arrow) records normally"""
        target_btn = self.window.hotkey_button_map.get('Right')
        
        # 1. Start recording
        QTest.mouseClick(target_btn, Qt.LeftButton)
        
        # 2. Enter 4-key combo
        QTest.keyClick(target_btn, Qt.Key_Right, Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier)
        
        # 3. Check GUI state
        expected_mod = "cmd" if sys.platform == 'darwin' else "ctrl"
        expected_display = f"{expected_mod} + alt + shift + right"
        self.assertEqual(target_btn.text().lower(), expected_display)
        
        # 4. Check saved data
        time.sleep(0.5)
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config['shortcuts']['Right']['pynput'], f"<{expected_mod}>+<alt>+<shift>+<right>")

    def test_hotkey_deletion(self):
        """Verify hotkey is reset by pressing Backspace during recording"""
        target_btn = self.window.hotkey_button_map.get('Right')

        # 1. Start recording
        QTest.mouseClick(target_btn, Qt.LeftButton)
        self.assertTrue(target_btn.is_recording)

        # 2. Press Backspace
        QTest.keyClick(target_btn, Qt.Key_Backspace)

        # 3. Check GUI state
        self.assertEqual(target_btn.text(), "Press hotkey")
        self.assertFalse(target_btn.is_recording)

        
        # 4. Verify file save
        time.sleep(0.5)
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config['shortcuts']['Right']['pynput'], "")

    def test_stale_config_filtering(self):
        """Verify stale feature filtering and migration"""
        # 1. Create stale config file
        stale_data = {
            "shortcuts": {
                "Left": {"pynput": "<ctrl>+l", "display": "CTRL+L", "mode": "left_half"},
                "DeleteMe": {"pynput": "<ctrl>+x", "display": "DELETE_ME", "mode": "none"}
            },
            "settings": {"gap": 10}
        }
        with open(TEST_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(stale_data, f)

        # 2. Load and create window
        from core import config_manager
        config_manager.load_config()
        new_window = self.gui.WinResizerPreferences()
        
        # 3. Verify migration
        btn = new_window.hotkey_button_map.get('Left')
        self.assertEqual(btn.text(), "ctrl + l")
        
        # 4. Verify cleanup
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            cleaned_config = json.load(f)
        self.assertEqual(cleaned_config["shortcuts"]["Left"]["display"], "ctrl + l")
        self.assertNotIn("DeleteMe", cleaned_config["shortcuts"])

    def test_gap_setting_persistence(self):
        """Verify Gap setting persistence"""
        new_gap_value = 15
        self.window.gap_spinbox.setValue(new_gap_value)
        
        time.sleep(0.5)
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config['settings']['gap'], new_gap_value)

    def test_clear_all_shortcuts_button(self):
        """Verify 'Clear All Hotkeys' button"""
        target_btn = self.window.hotkey_button_map['Left']
        QTest.mouseClick(target_btn, Qt.LeftButton)
        QTest.keyClick(target_btn, Qt.Key_K, Qt.ControlModifier)

        clear_btn = None
        for btn in self.window.findChildren(QPushButton):
            if btn.text() == "Clear All Hotkeys":
                clear_btn = btn
                break
        self.assertIsNotNone(clear_btn)

        with patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes):
            QTest.mouseClick(clear_btn, Qt.LeftButton)

        self.assertEqual(target_btn.text(), "Press hotkey")
        time.sleep(0.5)
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        self.assertEqual(saved_config['shortcuts']['Left']['pynput'], "")

if __name__ == "__main__":
    unittest.main()
