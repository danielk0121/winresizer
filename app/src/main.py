import sys
import os
from utils.logger import logger


def run_main():
    """
    앱 진입점.
    rumps 트레이 앱 + Flask 웹 서버 + 단축키 리스너를 시작한다.
    """
    logger.info("WinResizer starting...")

    from tray_app import TrayApp
    app = TrayApp()
    app.run()


if __name__ == "__main__":
    run_main()
