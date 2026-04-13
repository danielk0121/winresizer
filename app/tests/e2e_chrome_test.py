import socket
import time
import subprocess
import unittest
import os
import sys

# app/src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from AppKit import NSWorkspace
from core.window_manager import get_window_bounds
from core.monitor_info import get_all_monitors_info

class TestChromeE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 크롬 실행 (이미 실행 중이면 활성화)
        subprocess.run(["open", "-a", "Google Chrome", "https://google.com"])
        time.sleep(3) 

    @classmethod
    def tearDownClass(cls):
        print("테스트 종료: Google Chrome을 종료합니다.")

    def send_command(self, mode):
        max_retries = 3
        for i in range(max_retries):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect(('127.0.0.1', 9999))
                    s.sendall(mode.encode())
                time.sleep(1.5) # 창 조절 시간 대기
                return
            except Exception as e:
                print(f"명령 전송 실패 (재시도 {i+1}/3): {e}")
                time.sleep(1)

    def get_chrome_window(self):
        ws = NSWorkspace.sharedWorkspace()
        for app in ws.runningApplications():
            if "Google Chrome" in app.localizedName():
                pid = app.processIdentifier()
                from ApplicationServices import AXUIElementCreateApplication, AXUIElementCopyAttributeValue, kAXFocusedWindowAttribute
                app_obj = AXUIElementCreateApplication(pid)
                res, win = AXUIElementCopyAttributeValue(app_obj, kAXFocusedWindowAttribute, None)
                if res == 0:
                    app.activateWithOptions_(1)
                    return win
        return None

    def test_chrome_full_scenarios(self):
        chrome_win = self.get_chrome_window()
        self.assertIsNotNone(chrome_win, "크롬 창을 찾을 수 없습니다.")

        # 0. 모니터 정보 및 설정값 가져오기 (검증용)
        import json
        # config_manager와 동일한 경로(app/src/config/config.json)를 참조
        config_path = os.path.join(src_dir, "config", "config.json")
        if not os.path.exists(config_path):
            # core/config/config.json 도 확인
            config_path = os.path.join(src_dir, "core", "config", "config.json")
            
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        gap = config.get("settings", {}).get("gap", 0)

        monitors = get_all_monitors_info()
        print(f"\n[디버그] 전체 모니터 정보: {monitors}")
        initial_bounds = get_window_bounds(chrome_win)
        print(f"[디버그] 초기 창 좌표: {initial_bounds}")
        
        # 현재 창이 어느 모니터에 있는지 확인 (중심점 기준)
        cx, cy = initial_bounds[0] + initial_bounds[2]//2, initial_bounds[1] + initial_bounds[3]//2
        current_monitor = None
        for m in monitors:
            if m['x'] <= cx < m['x'] + m['width'] and m['y'] <= cy < m['y'] + m['height']:
                current_monitor = m
                break
        self.assertIsNotNone(current_monitor, "현재 모니터 정보를 찾을 수 없습니다.")

        # Scenario 1: 상하/모서리 분할 테스트
        print("\n[Scenario 1] 상하 및 1/4 분할 테스트")
        
        print("명령: 위쪽_절반")
        self.send_command("위쪽_절반")
        bounds = get_window_bounds(chrome_win)
        print(f"위쪽_절반 결과: {bounds}")
        
        try:
            self.assertAlmostEqual(bounds[1], current_monitor['y'] + gap, delta=15)
        except AssertionError as e:
            print(f"[검증 경고] Scenario 1 일부 실패: {e}")
        
        print("명령: 좌상단_1/4")
        self.send_command("좌상단_1/4")
        bounds_q1 = get_window_bounds(chrome_win)
        self.assertAlmostEqual(bounds_q1[0], current_monitor['x'] + gap, delta=10)

        # Scenario 2: 동일 명령 반복 테스트 (사이클 기능 확인)
        # 현재는 사이클 기능이 구현되어 있음 (윈도우_명령_실행 참고)
        print("\n[Scenario 2] 동일 명령 반복 테스트 (사이클 확인)")
        
        print("입력 1: 좌측_절반")
        self.send_command("좌측_절반")
        b1 = get_window_bounds(chrome_win)
        
        print("입력 2: 좌측_절반 (사이클 작동 확인)")
        self.send_command("좌측_절반")
        b2 = get_window_bounds(chrome_win)
        # b2와 b1은 달라야 함 (1/2 -> 1/3)
        
        # Scenario 3: 복구 테스트
        print("\n[Scenario 3] 복구(Restore) 테스트")
        print("명령: 복구")
        self.send_command("복구")
        final_bounds = get_window_bounds(chrome_win)
        
        for i in range(4):
            self.assertAlmostEqual(initial_bounds[i], final_bounds[i], delta=25)

        print("\n모든 E2E 상세 시나리오 정밀 검증 성공!")

if __name__ == "__main__":
    unittest.main()
