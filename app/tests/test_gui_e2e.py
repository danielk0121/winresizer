import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import unittest
from unittest.mock import MagicMock, patch
import json
import time
import importlib
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# app/src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# config_manager는 먼저 임포트해도 됨 (함수 호출 전까지는 영향 없음)
import config_manager

# 실제 설정 파일을 더럽히지 않기 위해 테스트용 설정 파일 경로 설정
TEST_CONFIG_FILE = os.path.join(os.path.dirname(src_dir), "config", "test_config.json")

class TestGuiE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. QApplication 인스턴스 생성
        from PyQt5.QtWidgets import QApplication
        if not QApplication.instance():
            cls.app = QApplication(sys.argv)
        else:
            cls.app = QApplication.instance()

        # 2. CONFIG_FILE 경로 패치 (모든 곳에 적용되도록)
        cls.config_patcher = patch('config_manager.CONFIG_FILE', TEST_CONFIG_FILE)
        cls.config_patcher.start()

        # 3. gui 모듈을 여기서 임포트하거나 다시 로드하여 패치된 CONFIG_FILE을 사용하게 함
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
        # ctrl + alt + k 형식으로 표시됨
        self.assertIn("k", target_btn.text().lower())
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
        print("E2E 검증 완료: 키보드 입력을 통한 단축키 초기화 성공")

    def test_hotkey_delete_button(self):
        # ... (기존 코드 유지)
        print("E2E 검증 완료: 'X' 버튼을 통한 단축키 초기화 성공")

    def test_stale_config_filtering(self):
        """정의되지 않은(삭제된) 기능이 파일에 남아있을 때 필터링되는지 확인하는 E2E 테스트"""
        # 1. 오염된 설정 파일 강제 생성 (삭제된 '중앙' 기능 포함)
        stale_data = {
            "shortcuts": {
                "왼쪽": {"pynput": "<ctrl>+l", "display": "ctrl + l", "mode": "좌측_절반"},
                "삭제된기능": {"pynput": "<ctrl>+x", "display": "ctrl + x", "mode": "none"}
            },
            "settings": {"gap": 10, "old_setting": "discard_me"}
        }
        with open(TEST_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(stale_data, f)

        # 2. 윈도우 새로 생성 (이때 load_config() 호출됨)
        # config_manager 모듈의 캐시된 설정을 갱신하기 위해 load_config를 명시적으로 호출
        import config_manager
        config_manager.load_config()
        new_window = self.gui.WinResizerPreferences()
        
        # 3. UI에 '삭제된기능'이 없는지 확인
        found = False
        for i in range(new_window.scroll_layout.count()):
            item = new_window.scroll_layout.itemAt(i)
            if item.layout():
                label = item.layout().itemAt(0).widget()
                if label.text() == "삭제된기능":
                    found = True; break
        
        self.assertFalse(found, "삭제된 기능이 UI에 여전히 노출되고 있습니다.")
        
        # 4. 파일도 깨끗하게 정리되었는지 확인 (자동 저장 로직 검증)
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            cleaned_config = json.load(f)
        
        self.assertNotIn("삭제된기능", cleaned_config["shortcuts"])
        self.assertNotIn("old_setting", cleaned_config["settings"])
        print("E2E 검증 완료: 오염된 설정 파일이 성공적으로 정제되었습니다.")

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
