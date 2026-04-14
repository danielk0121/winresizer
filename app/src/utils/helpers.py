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
        # PyInstaller로 빌드된 경우
        base_path = sys._MEIPASS
        # macOS 번들인 경우 sys._MEIPASS가 종종 Contents/Frameworks를 가리킴. 
        # 실제 리소스는 Contents/Resources에 있으므로 이를 보정.
        if "Contents/Frameworks" in base_path:
            resources_path = os.path.join(os.path.dirname(base_path), "Resources")
            if os.path.exists(os.path.join(resources_path, relative_path)):
                base_path = resources_path
    except AttributeError:
        # 로컬 환경인 경우
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    resolved_path = os.path.join(base_path, relative_path)
    # logger를 임포트하여 로그를 남깁니다. (순환 참조 방지를 위해 함수 내에서 임포트)
    try:
        from utils.logger import logger
        logger.debug(f"리소스 경로 해결: {relative_path} -> {resolved_path}")
    except Exception:
        pass

    return resolved_path
