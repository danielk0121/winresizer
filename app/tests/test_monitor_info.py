import unittest
from unittest.mock import MagicMock, patch
from app.src.monitor_info import get_all_monitors_info

class TestMonitorInfo(unittest.TestCase):
    @patch('app.src.monitor_info.NSScreen')
    def test_get_all_monitors_info_parsing(self, mock_nsscreen):
        # Mock NSScreen 객체 설정
        mock_screen = MagicMock()
        mock_frame = MagicMock()
        mock_frame.origin.x = 0
        mock_frame.origin.y = 0
        mock_frame.size.width = 1920
        mock_frame.size.height = 1080
        mock_screen.visibleFrame.return_value = mock_frame
        
        mock_nsscreen.screens.return_value = [mock_screen]
        
        # 실행
        monitors = get_all_monitors_info()
        
        # 검증
        self.assertEqual(len(monitors), 1)
        self.assertEqual(monitors[0]['x'], 0)
        self.assertEqual(monitors[0]['y'], 0)
        self.assertEqual(monitors[0]['width'], 1920)
        self.assertEqual(monitors[0]['height'], 1080)

if __name__ == "__main__":
    unittest.main()
