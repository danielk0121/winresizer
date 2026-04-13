import sys
import os

# app/src 경로를 시스템 경로에 추가하여 임포트 가능하게 함
sys.path.append(os.path.join(os.path.dirname(__file__), 'app', 'src'))

if __name__ == "__main__":
    from app.src.gui import WinResizerPreferences
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
