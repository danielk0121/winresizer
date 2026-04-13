import sys
from PyQt5.QtWidgets import QApplication
from gui import WinResizerPreferences
from utils.logger import logger

def run_main():
    """
    Main application entry point.
    Launches the GUI and background listener.
    """
    # 1. Logging setup
    logger.info("WinResizer starting...")
    
    # 2. PyQt5 application initialization
    app = QApplication(sys.argv)
    
    # 3. Main preferences window creation
    window = WinResizerPreferences()
    window.show()
    
    # 4. Event loop start
    sys.exit(app.exec_())

if __name__ == "__main__":
    run_main()
