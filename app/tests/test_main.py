import unittest
from unittest.mock import patch, MagicMock
from app.src.main import execute_command

class TestMainLogic(unittest.TestCase):
    @patch('app.src.main.get_all_monitors_info')
    @patch('app.src.main.calculate_window_position')
    @patch('app.src.main.get_active_window_object')
    @patch('app.src.main.set_window_bounds')
    def test_execute_command_flow(self, mock_set_bounds, mock_get_window, mock_calc_pos, mock_get_monitors):
        # 1. Mock 데이터 설정
        mock_get_monitors.return_value = [{"x": 0, "y": 0, "width": 1920, "height": 1080}]
        mock_calc_pos.return_value = (0, 0, 960, 1080) # 좌측 절반
        mock_get_window.return_value = "MockWindowObject"
        
        # 2. 실행
        execute_command("좌측_절반")
        
        # 3. 각 단계 호출 확인
        mock_get_monitors.assert_called_once()
        mock_calc_pos.assert_called_once_with((1920, 1080), "좌측_절반")
        mock_get_window.assert_called_once()
        mock_set_bounds.assert_called_once_with("MockWindowObject", 0, 0, 960, 1080)

    @patch('app.src.main.get_all_monitors_info')
    @patch('app.src.main.get_active_window_object')
    def test_execute_command_no_monitors(self, mock_get_window, mock_get_monitors):
        # 모니터 정보가 없을 때
        mock_get_monitors.return_value = []
        
        # 실행 (오류 없이 종료되어야 함)
        execute_command("좌측_절반")
        
        # 윈도우 찾기를 시도하지 않아야 함
        mock_get_window.assert_not_called()

if __name__ == "__main__":
    unittest.main()
