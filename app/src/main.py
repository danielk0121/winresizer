import sys
import os
from PyQt5.QtWidgets import QApplication, QMessageBox
from gui import WinResizerPreferences
from utils.logger import logger
from core.config_manager import CONFIG_FILE

def run_main():
    """
    Main application entry point.
    Launches the GUI and background listener.
    """
    # 1. Logging setup
    logger.info("WinResizer starting...")
    
    # 2. PyQt5 application initialization
    app = QApplication(sys.argv)
    
    # Check if config exists, if not notify user
    if not os.path.exists(CONFIG_FILE):
        QMessageBox.information(None, "환영합니다!", "WinResizer가 처음 실행되었습니다.\n설정 창에서 단축키를 확인하고 필요한 경우 변경해주세요.")
    
    # 3. Main preferences window creation
    app.setQuitOnLastWindowClosed(False)  # Keep app running when window is closed
    window = WinResizerPreferences()
    
    # 4. Event loop start
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_main()
