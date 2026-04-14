"""
커스텀 비율 창 조절 — window_controller 유효성 검사 테스트
"""
import unittest
from unittest.mock import patch, MagicMock
import os, sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from core.window_controller import parse_custom_mode, is_valid_custom_mode


class TestParseCustomMode(unittest.TestCase):

    def test_left_custom_parses(self):
        direction, pct = parse_custom_mode("left_custom:75")
        self.assertEqual(direction, "left")
        self.assertEqual(pct, 75)

    def test_right_custom_parses(self):
        direction, pct = parse_custom_mode("right_custom:30")
        self.assertEqual(direction, "right")
        self.assertEqual(pct, 30)

    def test_top_custom_parses(self):
        direction, pct = parse_custom_mode("top_custom:60")
        self.assertEqual(direction, "top")
        self.assertEqual(pct, 60)

    def test_bottom_custom_parses(self):
        direction, pct = parse_custom_mode("bottom_custom:1")
        self.assertEqual(direction, "bottom")
        self.assertEqual(pct, 1)

    def test_non_custom_returns_none(self):
        self.assertIsNone(parse_custom_mode("left_half"))
        self.assertIsNone(parse_custom_mode("maximize"))
        self.assertIsNone(parse_custom_mode("복구"))


class TestIsValidCustomMode(unittest.TestCase):

    def test_valid_range(self):
        self.assertTrue(is_valid_custom_mode("left_custom:1"))
        self.assertTrue(is_valid_custom_mode("left_custom:50"))
        self.assertTrue(is_valid_custom_mode("left_custom:99"))

    def test_zero_is_invalid(self):
        self.assertFalse(is_valid_custom_mode("left_custom:0"))

    def test_100_is_invalid(self):
        self.assertFalse(is_valid_custom_mode("left_custom:100"))

    def test_negative_is_invalid(self):
        self.assertFalse(is_valid_custom_mode("left_custom:-1"))

    def test_non_integer_is_invalid(self):
        self.assertFalse(is_valid_custom_mode("left_custom:abc"))
        self.assertFalse(is_valid_custom_mode("left_custom:7.5"))

    def test_non_custom_mode_is_invalid(self):
        self.assertFalse(is_valid_custom_mode("left_half"))


if __name__ == '__main__':
    unittest.main(verbosity=2)
