import unittest
from core.coordinate_calculator import calculate_window_position

class TestCoordinateCalculator(unittest.TestCase):
    def test_calculate_left_half(self):
        # 27인치 모니터 (2560x1440)의 좌측 50%
        screen_size = (2560, 1440)
        expected = (0, 0, 1280, 1440)
        actual = calculate_window_position(screen_size, "left_half")
        self.assertEqual(expected, actual)

    def test_calculate_right_half(self):
        # 27인치 모니터의 우측 50%
        screen_size = (2560, 1440)
        expected = (1280, 0, 1280, 1440)
        actual = calculate_window_position(screen_size, "right_half")
        self.assertEqual(expected, actual)

    # ── 커스텀 비율 ──────────────────────────────────────────

    def test_left_custom_75(self):
        """좌측 75% — x=0, 너비=screen_width*0.75"""
        screen_size = (2000, 1000)
        x, y, w, h = calculate_window_position(screen_size, "left_custom:75")
        self.assertAlmostEqual(x, 0, delta=1)
        self.assertAlmostEqual(y, 0, delta=1)
        self.assertAlmostEqual(w, 1500, delta=1)
        self.assertAlmostEqual(h, 1000, delta=1)

    def test_right_custom_30(self):
        """우측 30% — x=screen_width*0.70, 너비=screen_width*0.30"""
        screen_size = (2000, 1000)
        x, y, w, h = calculate_window_position(screen_size, "right_custom:30")
        self.assertAlmostEqual(x, 1400, delta=1)
        self.assertAlmostEqual(y, 0, delta=1)
        self.assertAlmostEqual(w, 600, delta=1)
        self.assertAlmostEqual(h, 1000, delta=1)

    def test_top_custom_60(self):
        """상단 60% — y=0, 높이=screen_height*0.60"""
        screen_size = (2000, 1000)
        x, y, w, h = calculate_window_position(screen_size, "top_custom:60")
        self.assertAlmostEqual(x, 0, delta=1)
        self.assertAlmostEqual(y, 0, delta=1)
        self.assertAlmostEqual(w, 2000, delta=1)
        self.assertAlmostEqual(h, 600, delta=1)

    def test_bottom_custom_40(self):
        """하단 40% — y=screen_height*0.60, 높이=screen_height*0.40"""
        screen_size = (2000, 1000)
        x, y, w, h = calculate_window_position(screen_size, "bottom_custom:40")
        self.assertAlmostEqual(x, 0, delta=1)
        self.assertAlmostEqual(y, 600, delta=1)
        self.assertAlmostEqual(w, 2000, delta=1)
        self.assertAlmostEqual(h, 400, delta=1)

    def test_custom_with_gap(self):
        """gap 적용 시 좌측 50% — gap=10"""
        screen_size = (2000, 1000)
        x, y, w, h = calculate_window_position(screen_size, "left_custom:50", gap=10)
        self.assertAlmostEqual(x, 10, delta=1)
        self.assertAlmostEqual(y, 10, delta=1)
        self.assertAlmostEqual(w, 980, delta=1)   # 1000 - gap*2
        self.assertAlmostEqual(h, 980, delta=1)   # 1000 - gap*2


if __name__ == "__main__":
    unittest.main()
