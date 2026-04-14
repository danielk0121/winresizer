import unittest
from unittest.mock import patch, MagicMock
import os, sys

# src 경로 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from core.window_controller import execute_window_command

class TestWindowOverflow(unittest.TestCase):

    @patch('core.window_controller.is_accessibility_trusted', return_value=True)
    @patch('core.window_controller.NSWorkspace')
    @patch('core.window_controller.get_active_window_object')
    @patch('core.window_controller.get_window_bounds')
    @patch('core.window_controller.get_all_monitors_info')
    @patch('core.window_controller.set_window_bounds')
    @patch('core.window_controller.config_manager.get_config')
    def test_right_alignment_overflow_fix(self, mock_get_config, mock_set_bounds, mock_monitors, mock_get_bounds, mock_get_window, mock_ns_workspace, mock_trusted):
        # 1. 환경 설정
        mock_get_config.return_value = {'settings': {'gap': 0}}
        
        mock_app = MagicMock()
        mock_app.localizedName.return_value = "TestApp"
        mock_ns_workspace.sharedWorkspace.return_value.frontmostApplication.return_value = mock_app
        
        mock_window = MagicMock()
        mock_get_window.return_value = mock_window
        
        # 현재 창 위치: 모니터 중앙 (1920x1080 모니터 기준)
        # 초기 상태 -> 정렬 판별용 (이미 정렬되어 있는지 확인 시) -> 수정 후 다시 확인용
        side_effects = [
            (800, 400, 300, 300), # 초기 상태 (현재 창 위치 확인용)
            (650, 0, 500, 1000),   # 정렬 판별용 (이미 정렬되어 있는지 확인 시) - 버그 상황 (너비가 500으로 고정됨)
            (650, 0, 500, 1000),   # 최종 검증용
        ]
        mock_get_bounds.side_effect = side_effects
        
        # 모니터 정보
        mock_monitors.return_value = [{'x': 0, 'y': 0, 'width': 1000, 'height': 1000}]
        
        # 3. 명령 실행
        execute_window_command("right_custom:35")
        
        # 4. 검증: 첫 번째 set_window_bounds 호출 (이론적 계산값)
        mock_set_bounds.assert_any_call(mock_window, 650.0, 0.0, 350.0, 1000.0)
        
        # 5. [중요] 버그 수정 후: 두 번째 set_window_bounds 호출 (Re-anchoring)
        # 1000(모니터우측) - 500(실제너비) = 500
        mock_set_bounds.assert_any_call(mock_window, 500.0, 0.0, 500.0, 1000.0)

    @patch('core.window_controller.is_accessibility_trusted', return_value=True)
    @patch('core.window_controller.NSWorkspace')
    @patch('core.window_controller.get_active_window_object')
    @patch('core.window_controller.get_window_bounds')
    @patch('core.window_controller.get_all_monitors_info')
    @patch('core.window_controller.set_window_bounds')
    @patch('core.window_controller.config_manager.get_config')
    def test_bottom_alignment_overflow_fix(self, mock_get_config, mock_set_bounds, mock_monitors, mock_get_bounds, mock_get_window, mock_ns_workspace, mock_trusted):
        # 1. 환경 설정
        mock_get_config.return_value = {'settings': {'gap': 0}}
        
        mock_app = MagicMock()
        mock_app.localizedName.return_value = "TestApp"
        mock_ns_workspace.sharedWorkspace.return_value.frontmostApplication.return_value = mock_app
        
        mock_window = MagicMock()
        mock_get_window.return_value = mock_window
        
        # 현재 창 위치: 모니터 중앙
        # 초기 상태 -> 정렬 판별용 -> 수정 후 다시 확인용
        side_effects = [
            (400, 400, 300, 300), 
            (0, 650, 1000, 500),   # 버그 상황: 높이가 500으로 고정되어 아래로 짤림 (650 + 500 = 1150)
            (0, 650, 1000, 500),   
        ]
        mock_get_bounds.side_effect = side_effects
        
        # 모니터 정보
        mock_monitors.return_value = [{'x': 0, 'y': 0, 'width': 1000, 'height': 1000}]
        
        # 3. 명령 실행
        execute_window_command("bottom_custom:35")
        
        # 4. 검증: 첫 번째 set_window_bounds 호출 (계산값 350.0)
        mock_set_bounds.assert_any_call(mock_window, 0.0, 650.0, 1000.0, 350.0)
        
        # 5. 검증: 두 번째 set_window_bounds 호출 (Re-anchoring)
        # 1000(모니터하단) - 500(실제높이) = 500
        mock_set_bounds.assert_any_call(mock_window, 0.0, 500.0, 1000.0, 500.0)

    @patch('core.window_controller.is_accessibility_trusted', return_value=True)
    @patch('core.window_controller.NSWorkspace')
    @patch('core.window_controller.get_active_window_object')
    @patch('core.window_controller.get_window_bounds')
    @patch('core.window_controller.get_all_monitors_info')
    @patch('core.window_controller.set_window_bounds')
    @patch('core.window_controller.get_saved_window_state')
    @patch('core.window_controller.config_manager.get_config')
    def test_monitor_cycling_from_overflow_state(self, mock_get_config, mock_get_saved, mock_set_bounds, mock_monitors, mock_get_bounds, mock_get_window, mock_ns_workspace, mock_trusted):
        # 1. 환경 설정
        mock_get_config.return_value = {'settings': {'gap': 0}}
        
        mock_app = MagicMock()
        mock_workspace = MagicMock()
        mock_workspace.frontmostApplication.return_value = mock_app
        mock_ns_workspace.sharedWorkspace.return_value = mock_workspace
        
        mock_window = MagicMock()
        mock_get_window.return_value = mock_window
        
        # 현재 상태: 우측으로 150px 짤린 상태 (x=650, w=500 -> right=1150, monitor_width=1000)
        mock_get_bounds.return_value = (650, 0, 500, 1000)
        
        # 저장된 상태 없음
        mock_get_saved.return_value = None
        
        # 모니터 정보: 2개 모니터
        monitor1 = {'x': 0, 'y': 0, 'width': 1000, 'height': 1000}
        monitor2 = {'x': 1000, 'y': 0, 'width': 1000, 'height': 1000}
        mock_monitors.return_value = [monitor1, monitor2]
        
        # 3. 명령 실행: 'right_custom:35' (계산된 x=650, w=350)
        execute_window_command("right_custom:35")
        
        # 4. 검증: 다음 모니터(monitor2)로 이동해야 함
        # 현재 짤린 상태라도 '이미 정렬됨'으로 인식되어야 함.
        # monitor2의 x=1000에서 시작해야 함.
        # saved_state가 없으면 현재 bounds(650,0,500,1000)를 기준으로 이동
        # rel_x = 650 - 0 = 650
        # new_x = 1000 + 650 = 1650
        # 하지만 다음 모니터(width=1000) 내로 Clamping 되므로:
        # new_x = min(1650, 1000 + 1000 - 500) = 1500
        mock_set_bounds.assert_called_with(mock_window, 1500, 0, 500, 1000)

if __name__ == '__main__':
    unittest.main()
