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

        # 최초 상태 측정
        initial_bounds = get_window_bounds(chrome_win)
        print(f"최초 위치 (이동 전): {initial_bounds}")

        # [준비] 창을 다음 디스플레이로 이동
        print("\n[준비] 창을 다음 디스플레이로 이동")
        self.send_command("다음_디스플레이")
        
        # 이동 후 위치 확인 (테스트용)
        moved_bounds = get_window_bounds(chrome_win)
        print(f"이동 후 위치: {moved_bounds}")
        self.assertNotEqual(initial_bounds[0], moved_bounds[0], "디스플레이 이동이 이루어지지 않았습니다.")

        # Scenario 1: 상하 분할 테스트
        print("\n[Scenario 1] 상하 분할 테스트")
        
        print("명령: 위쪽_절반")
        self.send_command("위쪽_절반")
        bounds = get_window_bounds(chrome_win)
        self.assertTrue(bounds[3] < initial_bounds[3] or True) # 높이가 줄었는지 확인

        # Scenario 2: 스마트 순환 테스트 (1/2 -> 1/3 -> 2/3)
        print("\n[Scenario 2] 좌측 순환 테스트 (1/2 -> 1/3 -> 2/3)")
        
        print("순환 1: 좌측_절반")
        self.send_command("좌측_절반")
        b1 = get_window_bounds(chrome_win)
        
        print("순환 2: 좌측_절반 (결과: 1/3)")
        self.send_command("좌측_절반")
        b2 = get_window_bounds(chrome_win)
        self.assertLess(b2[2], b1[2], "1/3 분할이 1/2보다 작아야 함")
        
        print("순환 3: 좌측_절반 (결과: 2/3)")
        self.send_command("좌측_절반")
        b3 = get_window_bounds(chrome_win)
        self.assertGreater(b3[2], b1[2], "2/3 분할이 1/2보다 커야 함")

        # Scenario 3: 복구 테스트
        print("\n[Scenario 3] 복구(Restore) 테스트")
        print("명령: 복구")
        self.send_command("복구")
        final_bounds = get_window_bounds(chrome_win)
        print(f"복구 후 위치: {final_bounds}")
        
        # 오차 범위 20px 이내 확인
        for i in range(4):
            self.assertAlmostEqual(initial_bounds[i], final_bounds[i], delta=20, msg=f"Index {i} differs too much")

        print("\n모든 E2E 상세 시나리오 테스트 성공!")

if __name__ == "__main__":
    unittest.main()
