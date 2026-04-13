import sys
import os

def apply_gap(x, y, w, h, gap):
    """
    주어진 좌표에 여백(Gap)을 적용합니다.
    """
    return (x + gap, y + gap, w - 2 * gap, h - 2 * gap)

def is_similar(b1, b2, tolerance=20):
    """
    두 영역(bounds)이 오차 범위 내에서 유사한지 확인합니다.
    """
    if not b1 or not b2:
        return False
    return all(abs(a - b) <= tolerance for a, b in zip(b1, b2))

def get_resource_path(relative_path):
    """
    PyInstaller 환경과 로컬 실행 환경 모두에서 리소스 파일의 절대 경로를 반환합니다.
    """
    try:
        # PyInstaller로 빌드된 경우, 임시 폴더 경로를 반환
        base_path = sys._MEIPASS
    except AttributeError:
        # 로컬 환경인 경우, 프로젝트 루트 폴더 기준 경로를 계산 (app/src/utils/helpers.py 기준)
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
    return os.path.join(base_path, relative_path)
