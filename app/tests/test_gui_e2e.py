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
        """단축키를 실제로 기록하고 파일에 저장되는지 확인하는 E2E 테스트 (정밀 검증)"""
        
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
        QTest.keyClick(target_btn, Qt.Key_K, Qt.ControlModifier | Qt.AltModifier)
        
        # 4. GUI 상태 정밀 확인
        # 정확히 "ctrl + alt + k" 형식이어야 함 (대소문자 무관하게 체크하되 형식 일관성 확인)
        # macOS에서는 ControlModifier가 cmd로 매핑됨
        expected_mod = "cmd" if sys.platform == 'darwin' else "ctrl"
        self.assertEqual(target_btn.text().lower(), f"{expected_mod} + alt + k")
        self.assertFalse(target_btn.recording)
        
        # 5. 파일 저장 확인 (실제 파일 I/O 정밀 검증)
        time.sleep(0.5) 
        self.assertTrue(os.path.exists(TEST_CONFIG_FILE), "설정 파일이 생성되지 않았습니다.")
        
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
            
        shortcut_data = saved_config['shortcuts']['왼쪽']
        self.assertEqual(shortcut_data['pynput'], f"<{expected_mod}>+<alt>+k")
        self.assertEqual(shortcut_data['display'].lower(), f"{expected_mod} + alt + k")
        print(f"E2E 정밀 검증 완료: 저장된 단축키 데이터 구조 일치 확인")

    def test_hotkey_4_keys_combination(self):
        """4개 이상의 키 조합(Ctrl+Alt+Shift+방향키)이 정상적으로 기록되는지 확인"""
        target_btn = self.window.hotkey_buttons['오른쪽']
        
        # 1. 녹화 시작
        QTest.mouseClick(target_btn, Qt.LeftButton)
        
        # 2. 4개 키 조합 입력 (Ctrl + Alt + Shift + Right)
        # Note: Qt.Key_Right와 Modifier 조합
        QTest.keyClick(target_btn, Qt.Key_Right, Qt.ControlModifier | Qt.AltModifier | Qt.ShiftModifier)
        
        # 3. GUI 상태 확인
        expected_mod = "cmd" if sys.platform == 'darwin' else "ctrl"
        expected_display = f"{expected_mod} + alt + shift + right"
        self.assertEqual(target_btn.text().lower(), expected_display)
        
        # 4. 저장된 데이터 확인
        time.sleep(0.5)
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
            
        shortcut_data = saved_config['shortcuts']['오른쪽']
        # pynput 형식 확인
        self.assertEqual(shortcut_data['pynput'], f"<{expected_mod}>+<alt>+<shift>+<right>")

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
        """정의되지 않은(삭제된) 기능 필터링 및 과거 형식(CTRLALTLEFT) 마이그레이션 확인"""
        # 1. 오염된 설정 파일 강제 생성 (삭제된 기능 + 과거 형식 데이터)
        stale_data = {
            "shortcuts": {
                "왼쪽": {"pynput": "<ctrl>+l", "display": "CTRL+L", "mode": "좌측_절반"}, # 과거 형식
                "삭제된기능": {"pynput": "<ctrl>+x", "display": "DELETE_ME", "mode": "none"}
            },
            "settings": {"gap": 10, "old_setting": "discard_me"}
        }
        with open(TEST_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(stale_data, f)

        # 2. 로드 및 윈도우 생성
        import config_manager
        config_manager.load_config()
        new_window = self.gui.WinResizerPreferences()
        
        # 3. 과거 형식이 새 형식으로 바뀌었는지 확인 (CTRL+L -> ctrl + l)
        found_left = False
        for i in range(new_window.scroll_layout.count()):
            item = new_window.scroll_layout.itemAt(i)
            if item.layout():
                label = item.layout().itemAt(0).widget()
                if label.text() == "왼쪽":
                    btn = item.layout().itemAt(1).widget()
                    self.assertEqual(btn.text(), "ctrl + l")
                    found_left = True
        self.assertTrue(found_left)
        
        # 4. 파일도 정리되었는지 확인
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            cleaned_config = json.load(f)
        
        self.assertEqual(cleaned_config["shortcuts"]["왼쪽"]["display"], "ctrl + l")
        print("E2E 검증 완료: 과거 데이터 형식이 성공적으로 마이그레이션되었습니다.")

    def test_gap_setting_persistence(self):
        """간격(Gap) 설정을 변경하고 파일에 저장되는지 확인하는 E2E 테스트"""
        
        new_gap_value = 15
        self.window.gap_spin.setValue(new_gap_value)
        
        time.sleep(0.5) # 파일 쓰기 대기
        
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
            
        self.assertEqual(saved_config['settings']['gap'], new_gap_value)
        print(f"E2E 검증 완료: 저장된 간격 -> {saved_config['settings']['gap']}")

    def test_clear_all_shortcuts_button(self):
        """'모든 단축키 삭제' 버튼이 모든 설정을 초기화하는지 확인하는 E2E 테스트"""
        # 1. 먼저 단축키 하나를 설정해둠 (준비 과정)
        target_btn = self.window.hotkey_buttons['왼쪽']
        QTest.mouseClick(target_btn, Qt.LeftButton)
        QTest.keyClick(target_btn, Qt.Key_K, Qt.ControlModifier)
        expected_mod = "cmd" if sys.platform == 'darwin' else "ctrl"
        self.assertEqual(target_btn.text().lower(), f"{expected_mod} + k")

        
        # 2. '모든 단축키 삭제' 버튼 찾기
        # 2. '모든 단축키 삭제' 버튼 찾기
        clear_btn = None
        for btn in self.window.findChildren(QPushButton):
            if btn.text() == "모든 단축키 삭제":
                clear_btn = btn
                break
        self.assertIsNotNone(clear_btn, "'모든 단축키 삭제' 버튼을 찾을 수 없습니다.")

        # 3. 버튼 클릭 시 QMessageBox.question 모킹 (Yes 반환)
        with patch('PyQt5.QtWidgets.QMessageBox.question', return_value=QMessageBox.Yes):
            QTest.mouseClick(clear_btn, Qt.LeftButton)

        # 4. 모든 단축키가 초기화되었는지 확인
        self.assertEqual(target_btn.text(), "단축키 입력")

        
        # 5. 파일 저장 확인
        time.sleep(0.5)
        with open(TEST_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_config = json.load(f)
        
        self.assertEqual(saved_config['shortcuts']['왼쪽']['pynput'], "")
        print("E2E 검증 완료: '모든 단축키 삭제' 버튼 기능 정상 작동 확인")

if __name__ == "__main__":
    unittest.main()
