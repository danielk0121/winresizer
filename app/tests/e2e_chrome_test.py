import socket
import time
import subprocess
import unittest
from AppKit import NSWorkspace
from app.src.window_manager import get_window_bounds
from app.src.monitor_info import get_all_monitors_info

class TestChromeE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["open", "-a", "Google Chrome", "https://google.com"])
        time.sleep(3) 

    def send_command(self, mode):
        max_retries = 5
        for i in range(max_retries):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect(('localhost', 9999))
                    s.sendall(mode.encode())
                time.sleep(1.5) # 창 조절 시간 대기
                return
            except:
                time.sleep(2)

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

    def test_chrome_resize_flow(self):
        chrome_win = self.get_chrome_window()
        self.assertIsNotNone(chrome_win, "크롬 창을 찾을 수 없습니다.")

        # 1. 초기 위치 저장 및 가로 모니터(X=0 부근)로 이동 시도
        # 세로 모니터(폭 1080)에서는 최소 폭 제한 때문에 테스트가 실패할 수 있음
        print("테스트 준비: 창을 가로 모니터로 이동")
        self.send_command("다음_디스플레이")
        time.sleep(1)
        
        initial_bounds = get_window_bounds(chrome_win)
        print(f"가로 모니터 이동 후 초기 위치: {initial_bounds}")

        # 2. 좌측 절반 명령 전송
        print("테스트 1: 좌측 절반 명령 전송")
        self.send_command("좌측_절반")
        time.sleep(1.5)
        bounds_1 = get_window_bounds(chrome_win)
        print(f"좌측 절반 적용 후: {bounds_1}")
        self.assertNotEqual(initial_bounds, bounds_1, "창 위치/크기가 변경되지 않았습니다.")

        # 3. 스마트 순환 (좌측 절반 -> 좌측 1/3)
        print("테스트 2: 다시 좌측 절반 명령 전송 (순환)")
        self.send_command("좌측_절반")
        bounds_2 = get_window_bounds(chrome_win)
        print(f"좌측 1/3(순환) 적용 후: {bounds_2}")
        self.assertNotEqual(bounds_1, bounds_2, "스마트 순환이 작동하지 않았습니다 (크기 불변).")

        # 4. 복구 테스트
        print("테스트 3: 복구 명령 전송")
        self.send_command("복구")
        bounds_final = get_window_bounds(chrome_win)
        print(f"복구 적용 후: {bounds_final}")
        # 복구 시 오차 범위 10px 내외 확인
        self.assertTrue(all(abs(a - b) < 10 for a, b in zip(initial_bounds, bounds_final)), "복구된 위치가 초기 위치와 다릅니다.")

        print("E2E 테스트 모든 시나리오 성공!")

if __name__ == "__main__":
    unittest.main()
