import sys
import os

# 1. 현재 파일(main.py)의 절대 경로를 기준으로 app/src 폴더를 찾음
current_file_path = os.path.abspath(__file__)
src_dir = os.path.dirname(current_file_path)
project_root = os.path.dirname(os.path.dirname(src_dir))

# 2. sys.path의 맨 앞에 app/src를 추가하여 내부 모듈(gui, window_manager 등)을 직접 임포트 가능하게 함
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# 3. 프로젝트 루트도 추가하여 'app.src.xxx' 형태의 임포트도 혹시 모를 상황에 대비해 지원
if project_root not in sys.path:
    sys.path.append(project_root)

if __name__ == "__main__":
    # 이제 'app.src.' 없이 직접 임포트 가능
    from gui import WinResizerPreferences
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
