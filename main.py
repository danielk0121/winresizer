import subprocess
import sys
import os

if __name__ == "__main__":
    # PYTHONPATH를 설정하여 app/src를 모듈로 인식하게 함
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), "app", "src")
    
    # app/src/main.py 실행
    main_path = os.path.join("app", "src", "main.py")
    subprocess.run([sys.executable, main_path], env=env)
