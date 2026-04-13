import unittest
from unittest.mock import patch, MagicMock
from core.window_controller import execute_window_command as execute_command

class TestMainLogic(unittest.TestCase):
    @patch('core.window_controller.is_accessibility_trusted')
    @patch('core.window_controller.NSWorkspace')
    @patch('core.window_controller.get_active_window_object')
    @patch('core.window_controller.get_window_bounds')
    @patch('core.window_controller.get_all_monitors_info')
    @patch('core.window_controller.calculate_window_position')
    @patch('core.window_controller.set_window_bounds')
    @patch('core.window_controller.config_manager.get_config')
    def test_execute_command_flow(self, mock_get_config, mock_set_bounds, mock_calc_pos, mock_get_monitors, mock_get_bounds, mock_get_window, mock_nsworkspace, mock_is_trusted):
        # 1. Mock 데이터 설정
        mock_is_trusted.return_value = True
        mock_active_app = MagicMock()
        mock_active_app.localizedName.return_value = "TestApp"
        mock_nsworkspace.sharedWorkspace.return_value.frontmostApplication.return_value = mock_active_app
        mock_get_config.return_value = {'settings': {'gap': 0}}
        
        mock_get_monitors.return_value = [{"x": 0, "y": 0, "width": 1920, "height": 1080}]
        mock_calc_pos.return_value = (0, 0, 960, 1080) # 좌측 절반
        mock_get_window.return_value = "MockWindowObject"
        mock_get_bounds.return_value = (100, 100, 500, 500)
        
        # 2. 실행
        execute_command("좌측_절반")
        
        # 3. 각 단계 호출 확인
        mock_is_trusted.assert_called_once()
        mock_get_monitors.assert_called()
        mock_calc_pos.assert_called()
        mock_get_window.assert_called_once()
        mock_set_bounds.assert_called()

    @patch('core.window_controller.is_accessibility_trusted')
    def test_execute_command_no_trust(self, mock_is_trusted):
        # 권한이 없을 때
        mock_is_trusted.return_value = False
        
        # 실행 (오류 없이 종료되어야 함)
        execute_command("좌측_절반")
        
        # 더 이상 진행되지 않아야 함
        mock_is_trusted.assert_called_once()

if __name__ == "__main__":
    unittest.main()
