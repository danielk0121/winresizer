import unittest
from app.src.coordinate_calculator import calculate_window_position

class TestCoordinateCalculator(unittest.TestCase):
    def test_calculate_left_half(self):
        # 27인치 모니터 (2560x1440)의 좌측 50%
        screen_size = (2560, 1440)
        expected = (0, 0, 1280, 1440)
        actual = calculate_window_position(screen_size, "좌측_절반")
        self.assertEqual(expected, actual)

    def test_calculate_right_half(self):
        # 27인치 모니터의 우측 50%
        screen_size = (2560, 1440)
        expected = (1280, 0, 1280, 1440)
        actual = calculate_window_position(screen_size, "우측_절반")
        self.assertEqual(expected, actual)

    def test_calculate_center_fixed(self):
        # 27인치 모니터 중앙에 1200x800 배치
        screen_size = (2560, 1440)
        expected = (680, 320, 1200, 800) # (2560-1200)/2, (1440-800)/2
        actual = calculate_window_position(screen_size, "중앙_고정")
        self.assertEqual(expected, actual)

if __name__ == "__main__":
    unittest.main()
