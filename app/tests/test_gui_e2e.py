import sys
import os
import unittest
import json
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# app/src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from gui import WinResizerPreferences, HotkeyButton
import config_manager

# 실제 설정 파일을 더럽히지 않기 위해 테스트용 설정 파일 경로 설정
TEST_CONFIG_FILE = os.path.join(os.path.dirname(src_dir), "config", "test_config.json")

class TestGuiE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 테스트 실행을 위한 단일 QApplication 인스턴스 생성
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()
            
        # config_manager의 CONFIG_FILE 경로를 테스트용으로 변경
        cls.original_config_file = config_manager.CONFIG_FILE
        config_manager.CONFIG_FILE = TEST_CONFIG_FILE
        
        # 테스트용 기본 설정 파일 생성
        if os.path.exists(TEST_CONFIG_FILE):
            os.remove(TEST_CONFIG_FILE)
            
    @classmethod
    def tearDownClass(cls):
        # 테스트 완료 후 원상복구 및 임시 파일 삭제
        config_manager.CONFIG_FILE = cls.original_config_file
        if os.path.exists(TEST_CONFIG_FILE):
            os.remove(TEST_CONFIG_FILE)

    def setUp(self):
        # 매 테스트마다 새로운 윈도우 인스턴스 생성
        self.window = WinResizerPreferences()

    def test_hotkey_recording_and_persistence(self):
        """단축키를 실제로 기록하고 파일에 저장되는지 확인하는 E2E 테스트"""
        
        # 1. '왼쪽' 단축키 버튼 찾기
        target_btn = None
        for i in range(self.window.scroll_layout.count()):
            item = self.window.scroll_layout.itemAt(i)
            if item.layout():
                label = item.layout().itemAt(0).widget()
                if label.text() == "왼쪽":
                    target_btn = item.layout().itemAt(1).widget()
                    break
        
        self.assertIsNotNone(target_btn, "'왼쪽' 단축키 버튼을 찾을 수 없습니다.")
        
        # 2. 버튼 클릭 (녹화 시작)
        QTest.mouseClick(target_btn, Qt.LeftButton)
        self.assertEqual(target_btn.text(), "입력 대기...")
        self.assertTrue(target_btn.recording)
        
        # 3. 키 입력 시뮬레이션 (Ctrl + Alt + K)
        # QTest.keyClick은 실제 이벤트를 발생시킴
        # modifiers와 함께 K 키 누름
        QTest.keyClick(target_btn, Qt.Key_K, Qt.ControlModifier | Qt.AltModifier)
        
        # 4. GUI 상태 확인
        # ⌃⌥K 또는 ⌃⌥ + K 형태일 수 있음. PK 생성 로직에 따라 다름.
        self.assertIn("K", target_btn.text())
        self.assertFalse(target_btn.recording)
        
        # 5. 파일 저장 확인 (실제 파일 I/O 검증)
        time.sleep(0.5) # 파일 쓰기 대기
        self.assertTrue(os.path.exists(TEST_CONFIG_FILE), "설정 파일이 생성되지 않았습니다.")
        
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
            
        shortcut_data = saved_config['shortcuts']['왼쪽']
        self.assertEqual(shortcut_data['pynput'], "<ctrl>+<alt>+k")
        print(f"E2E 검증 완료: 저장된 단축키 -> {shortcut_data['pynput']}")

    def test_hotkey_deletion(self):
        """단축키 녹화 중 Backspace를 눌러 초기화되는지 확인하는 E2E 테스트"""
        # 1. '오른쪽' 단축키 버튼 찾기
        target_btn = None
        for i in range(self.window.scroll_layout.count()):
            item = self.window.scroll_layout.itemAt(i)
            if item.layout():
                label = item.layout().itemAt(0).widget()
                if label.text() == "오른쪽":
                    target_btn = item.layout().itemAt(1).widget()
                    break
        
        self.assertIsNotNone(target_btn, "'오른쪽' 단축키 버튼을 찾을 수 없습니다.")
        
        # 2. 버튼 클릭 (녹화 시작)
        QTest.mouseClick(target_btn, Qt.LeftButton)
        self.assertTrue(target_btn.recording)
        
        # 3. Backspace 키 입력 시뮬레이션
        QTest.keyClick(target_btn, Qt.Key_Backspace)
        
        # 4. GUI 상태 확인
        self.assertEqual(target_btn.text(), "단축키 입력")
        self.assertFalse(target_btn.recording)
        
        # 5. 파일 저장 확인
        time.sleep(0.5)
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
            
        self.assertEqual(saved_config['shortcuts']['오른쪽']['pynput'], "")
        self.assertEqual(saved_config['shortcuts']['오른쪽']['display'], "단축키 입력")
        print("E2E 검증 완료: 단축키가 성공적으로 초기화되었습니다.")

    def test_gap_setting_persistence(self):
        """간격(Gap) 설정을 변경하고 파일에 저장되는지 확인하는 E2E 테스트"""
        
        new_gap_value = 15
        self.window.gap_spin.setValue(new_gap_value)
        
        time.sleep(0.5) # 파일 쓰기 대기
        
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
            
        self.assertEqual(saved_config['settings']['gap'], new_gap_value)
        print(f"E2E 검증 완료: 저장된 간격 -> {saved_config['settings']['gap']}")

if __name__ == "__main__":
    unittest.main()
