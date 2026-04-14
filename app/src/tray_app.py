import rumps
import subprocess
import ApplicationServices
from utils.logger import logger
from utils.helpers import get_resource_path
from web_server import run_server, open_browser
from core.hotkey_listener import HotkeyListenerThread

class TrayApp(rumps.App):
    """
    macOS 메뉴바 트레이 앱.
    rumps 기반으로 PyQt5 없이 동작한다.
    """
    def __init__(self):
        # PyInstaller BUNDLE 모드에서는 리소스 루트('.')에 파일이 위치함
        icon_path = get_resource_path("tray_icon.png")
        logger.info(f"트레이 앱 초기화 시작 - 아이콘 경로: {icon_path}")
        if not os.path.exists(icon_path):
            logger.error(f"아이콘 파일이 존재하지 않습니다: {icon_path}")
            icon_path = None
        
        super().__init__("WinResizer", icon=icon_path, template=True, quit_button=None)

        self.menu = [
            rumps.MenuItem("설정 (Preferences...)", callback=self.open_settings),
            None,  # 구분선
            rumps.MenuItem("종료 (Quit)", callback=self.quit_app),
        ]

        # 단축키 리스너 및 웹 서버 초기화 (지연 실행 고려)
        self.listener = None
        self.flask_app = None
        self.web_port = None
        
        logger.info("트레이 앱 초기화 완료")

    @rumps.clicked("설정 (Preferences...)")
    def open_settings(self, _):
        """브라우저로 설정 페이지 오픈"""
        if self.web_port:
            open_browser(port=self.web_port)
        else:
            logger.error("웹 서버가 아직 준비되지 않았습니다.")

    @rumps.notifications
    def on_notification(self, notification):
        logger.debug(f"알림 수신: {notification}")

    def setup_backend(self, _timer=None):
        """백엔드 서비스 시작 (app.run() 이후에 호출됨)"""
        try:
            logger.info("백엔드 서비스 시작 중...")
            # 접근성 권한 확인
            self._check_permissions()

            # 단축키 리스너 시작
            self.listener = HotkeyListenerThread()
            self.listener.start()

            # Flask 웹 서버 시작 (40000번대 랜덤 포트)
            self.flask_app, self.web_port = run_server()
            logger.info(f"백엔드 서비스 시작 완료 (Port: {self.web_port})")
        except Exception as e:
            logger.exception(f"백엔드 서비스 시작 중 오류 발생: {e}")

    def run(self, **kwargs):
        """rumps 앱 실행 전 백엔드 설정을 위해 오버라이드 (또는 @rumps.timer 사용)"""
        # rumps는 별도의 초기화 콜백이 없으므로 타이머를 이용해 1초 후 백엔드 실행
        timer = rumps.Timer(self.setup_backend, 1)
        timer.start()
        super().run(**kwargs)

    def _check_permissions(self):
        if not ApplicationServices.AXIsProcessTrusted():
            logger.warning("손쉬운 사용 권한 없음. 시스템 설정으로 이동합니다.")
            subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])

    def open_settings(self, _):
        """브라우저로 설정 페이지 오픈"""
        if self.web_port:
            open_browser(port=self.web_port)
        else:
            logger.error("웹 서버가 아직 준비되지 않았습니다.")

    def quit_app(self, _):
        """앱 종료"""
        if self.listener:
            self.listener.stop()
        logger.info("WinResizer 종료")
        rumps.quit_application()
