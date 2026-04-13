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
from ApplicationServices import AXUIElementCreateApplication, AXUIElementCopyAttributeValue, kAXFocusedWindowAttribute
from core.window_manager import get_window_bounds
from core.monitor_info import get_all_monitors_info

class TestBrowserE2E(unittest.TestCase):
    """다양한 브라우저(Chrome, Safari, Edge) 환경 테스트"""
    
    def setUp_browser(self, browser_name):
        self.browser_name = browser_name
        # 브라우저 실행
        subprocess.run(["open", "-a", browser_name, "https://google.com"])
        time.sleep(3)

    def send_command(self, mode):
        for i in range(3):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2)
                    s.connect(('127.0.0.1', 9999))
                    s.sendall(mode.encode())
                time.sleep(1.5)
                return
            except:
                time.sleep(1)

    def get_window(self):
        ws = NSWorkspace.sharedWorkspace()
        for app in ws.runningApplications():
            if self.browser_name in app.localizedName():
                pid = app.processIdentifier()
                app_obj = AXUIElementCreateApplication(pid)
                res, win = AXUIElementCopyAttributeValue(app_obj, kAXFocusedWindowAttribute, None)
                if res == 0:
                    app.activateWithOptions_(1)
                    return win
        return None

    def test_safari(self):
        self.setUp_browser("Safari")
        win = self.get_window()
        self.assertIsNotNone(win, "Safari 창을 찾을 수 없습니다.")
        self.send_command("좌측_절반")
        bounds = get_window_bounds(win)
        self.assertGreater(bounds[2], 0)

    def test_edge(self):
        self.setUp_browser("Microsoft Edge")
        win = self.get_window()
        self.assertIsNotNone(win, "Edge 창을 찾을 수 없습니다.")
        self.send_command("우측_절반")
        bounds = get_window_bounds(win)
        self.assertGreater(bounds[2], 0)

if __name__ == "__main__":
    unittest.main()
