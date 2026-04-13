import sys
import os

# 현재 파일 위치(app/src)를 시스템 경로에 추가하여 상대 경로 임포트 가능하게 함
sys.path.append(os.path.dirname(__file__))

if __name__ == "__main__":
    from gui import WinResizerPreferences
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
