import rumps
import subprocess
import ApplicationServices
import os
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
        # 1. 아이콘 경로 결정
        icon_path = get_resource_path("tray_icon.png")
        logger.info(f"트레이 앱 초기화 시작 (아이콘 경로: {icon_path})")
        
        if not os.path.exists(icon_path):
            logger.warning(f"아이콘 파일 없음: {icon_path}")
            icon_path = None
        
        # 2. rumps.App 초기화 (여기가 멈춤 포인트)
        try:
            logger.info("rumps.App super().__init__ 진입")
            super().__init__("WinResizer", icon=icon_path, template=True, quit_button=None)
            logger.info("rumps.App super().__init__ 통과")
        except Exception as e:
            logger.error(f"rumps 초기화 에러: {e}. 아이콘 없이 재시도.")
            super().__init__("WinResizer", quit_button=None)

        # 3. 메뉴 구성
        self.menu = [
            rumps.MenuItem("설정 (Preferences...)", callback=self.open_settings),
            None,  # 구분선
            rumps.MenuItem("종료 (Quit)", callback=self.quit_app),
        ]
        logger.info("트레이 메뉴 구성 완료")

        # 접근성 권한 확인
        self._check_permissions()

        # 단축키 리스너 시작
        self.listener = HotkeyListenerThread()
        self.listener.start()

        # Flask 웹 서버 시작 (40000번대 랜덤 포트)
        self.flask_app, self.web_port = run_server()
        logger.info(f"WinResizer 백엔드 서비스 준비 완료 (Port: {self.web_port})")

    def _check_permissions(self):
        if not ApplicationServices.AXIsProcessTrusted():
            logger.warning("손쉬운 사용 권한 없음. 설정에서 권한을 허용해 주세요.")
            # 알림이나 자동 오픈을 제거하여 사용자 방해를 최소화함

    def open_settings(self, _):
        """브라우저로 설정 페이지 오픈"""
        if hasattr(self, 'web_port') and self.web_port:
            open_browser(port=self.web_port)
        else:
            logger.error("웹 서버가 준비되지 않았습니다.")

    def quit_app(self, _):
        """앱 종료"""
        if hasattr(self, 'listener') and self.listener:
            self.listener.stop()
        logger.info("WinResizer 종료")
        rumps.quit_application()
