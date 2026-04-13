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
