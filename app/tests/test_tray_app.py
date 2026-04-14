import unittest
from unittest.mock import patch, MagicMock


class TestTrayApp(unittest.TestCase):
    """rumps 기반 트레이 앱 검증"""

    @patch('rumps.App.__init__', return_value=None)
    def test_tray_app_importable(self, mock_init):
        """TrayApp 클래스가 import 가능한지 확인"""
        from tray_app import TrayApp
        self.assertTrue(callable(TrayApp))

    @patch('rumps.App.__init__', return_value=None)
    def test_tray_app_has_open_settings(self, mock_init):
        """TrayApp에 설정 열기 메뉴 메서드가 있는지 확인"""
        from tray_app import TrayApp
        self.assertTrue(hasattr(TrayApp, 'open_settings'))

    @patch('rumps.App.__init__', return_value=None)
    def test_tray_app_has_quit(self, mock_init):
        """TrayApp에 종료 메서드가 있는지 확인"""
        from tray_app import TrayApp
        self.assertTrue(hasattr(TrayApp, 'quit_app'))

    @patch('rumps.App.__init__', return_value=None)
    @patch('web_server.open_browser')
    def test_open_settings_calls_browser(self, mock_browser, mock_init):
        """설정 열기 시 브라우저가 열리는지 확인"""
        from tray_app import TrayApp
        app = TrayApp.__new__(TrayApp)
        app.web_port = 42000  # 랜덤 포트 mock
        app.open_settings(None)
        mock_browser.assert_called_once_with(port=42000)


if __name__ == '__main__':
    unittest.main()
