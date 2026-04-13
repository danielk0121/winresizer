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
from window_manager import get_window_bounds
from monitor_info import get_all_monitors_info

class TestChromeE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 크롬 실행 (이미 실행 중이면 활성화)
        subprocess.run(["open", "-a", "Google Chrome", "https://google.com"])
        time.sleep(3) 

    @classmethod
    def tearDownClass(cls):
        print("테스트 종료: Google Chrome을 종료합니다.")
        # 테스트 완료 후 크롬 종료 (원치 않으면 주석 처리 가능)
        # subprocess.run(["osascript", "-e", 'quit app "Google Chrome"'])

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
        
        # 정밀 검증 (Gap 반영): y좌표는 모니터 시작점 + gap, 너비는 전체 - gap*2, 높이는 절반 - gap*1.5
        self.assertAlmostEqual(bounds[1], current_monitor['y'] + gap, delta=10)
        self.assertAlmostEqual(bounds[2], current_monitor['width'] - (gap * 2), delta=20)
        self.assertAlmostEqual(bounds[3], current_monitor['height'] / 2 - (gap * 1.5), delta=30)
        
        print("명령: 좌상단_1/4")
        self.send_command("좌상단_1/4")
        bounds_q1 = get_window_bounds(chrome_win)
        self.assertAlmostEqual(bounds_q1[0], current_monitor['x'] + gap, delta=10)
        self.assertAlmostEqual(bounds_q1[2], current_monitor['width'] / 2 - (gap * 1.5), delta=20)
        self.assertAlmostEqual(bounds_q1[3], current_monitor['height'] / 2 - (gap * 1.5), delta=20)

        print("명령: 우하단_1/4")
        self.send_command("우하단_1/4")
        bounds_q4 = get_window_bounds(chrome_win)
        # x좌표는 모니터 중간 + gap*0.5, y좌표는 모니터 중간 + gap*0.5
        self.assertAlmostEqual(bounds_q4[0], current_monitor['x'] + current_monitor['width']/2 + (gap * 0.5), delta=20)
        self.assertAlmostEqual(bounds_q4[1], current_monitor['y'] + current_monitor['height']/2 + (gap * 0.5), delta=20)

        # Scenario 2: 스마트 순환 테스트 (1/2 -> 1/3 -> 2/3)
        print("\n[Scenario 2] 좌측 순환 테스트 (1/2 -> 1/3 -> 2/3)")
        
        print("순환 1: 좌측_절반 (결과: 1/2)")
        self.send_command("좌측_절반")
        b1 = get_window_bounds(chrome_win)
        self.assertAlmostEqual(b1[2], current_monitor['width'] / 2 - (gap * 1.5), delta=20)
        
        print("순환 2: 좌측_절반 (결과: 1/3)")
        self.send_command("좌측_절반")
        b2 = get_window_bounds(chrome_win)
        self.assertAlmostEqual(b2[2], current_monitor['width'] / 3 - (gap * 1.5), delta=20)
        
        print("순환 3: 좌측_절반 (결과: 2/3)")
        self.send_command("좌측_절반")
        b3 = get_window_bounds(chrome_win)
        # 2/3 분할 시 너비: 2 * (w//3) - gap*1.0 (coordinate_calculator 로직 참고)
        self.assertAlmostEqual(b3[2], (current_monitor['width'] // 3) * 2 - (gap * 1.0), delta=20)

        # Scenario 3: 복구 테스트
        print("\n[Scenario 3] 복구(Restore) 테스트")
        print("명령: 복구")
        self.send_command("복구")
        final_bounds = get_window_bounds(chrome_win)
        
        for i in range(4):
            self.assertAlmostEqual(initial_bounds[i], final_bounds[i], delta=25, msg=f"Index {i} differs too much from initial")

        print("\n모든 E2E 상세 시나리오 정밀 검증 성공!")

if __name__ == "__main__":
    unittest.main()
