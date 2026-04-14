import rumps
import subprocess
import ApplicationServices
from utils.logger import logger
from utils.helpers import get_resource_path
from web_server import run_server, open_browser
from core.hotkey_listener import HotkeyListenerThread

WEB_PORT = 5000


class TrayApp(rumps.App):
    """
    macOS 메뉴바 트레이 앱.
    rumps 기반으로 PyQt5 없이 동작한다.
    """
    def __init__(self):
        icon_path = get_resource_path("app/src/ui/tray_icon.png")
        super().__init__("WinResizer", icon=icon_path, quit_button=None)

        self.menu = [
            rumps.MenuItem("설정 (Preferences...)", callback=self.open_settings),
            None,  # 구분선
            rumps.MenuItem("종료 (Quit)", callback=self.quit_app),
        ]

        # 접근성 권한 확인
        self._check_permissions()

        # 단축키 리스너 시작
        self.listener = HotkeyListenerThread()
        self.listener.start()

        # Flask 웹 서버 시작
        self.flask_app = run_server(port=WEB_PORT, listener=self.listener)

    def _check_permissions(self):
        if not ApplicationServices.AXIsProcessTrusted():
            logger.warning("손쉬운 사용 권한 없음. 시스템 설정으로 이동합니다.")
            subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])

    def open_settings(self, _):
        """브라우저로 설정 페이지 오픈"""
        open_browser(port=WEB_PORT)

    def quit_app(self, _):
        """앱 종료"""
        if self.listener:
            self.listener.stop()
        logger.info("WinResizer 종료")
        rumps.quit_application()
