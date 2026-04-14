import unittest
import json
import os
from unittest.mock import patch


class TestWebUIE2E(unittest.TestCase):
    """웹 UI 기반 E2E 검증 (test_gui_e2e.py, test_tray_e2e.py, test_hotkey_swap_test.py 대체)"""

    def setUp(self):
        from web_server import create_app
        self.app = create_app()
        self.client = self.app.test_client()

    @patch('core.config_manager.save_config')
    def test_hotkey_save_and_persistence(self, mock_save):
        """단축키 변경 후 저장 시 config에 반영되는지 확인"""
        payload = {
            'shortcuts': {
                'Left': {'pynput': '<cmd>+<alt>+k', 'display': 'cmd + alt + k', 'mode': 'left_half'}
            },
            'settings': {'gap': 5}
        }
        res = self.client.post('/api/config',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        saved = mock_save.call_args[0][0]
        self.assertEqual(saved['shortcuts']['Left']['pynput'], '<cmd>+<alt>+k')
        self.assertEqual(saved['shortcuts']['Left']['display'], 'cmd + alt + k')

    @patch('core.config_manager.save_config')
    def test_hotkey_deletion(self, mock_save):
        """단축키 삭제(빈 문자열) 저장이 정상 처리되는지 확인"""
        payload = {
            'shortcuts': {
                'Left': {'pynput': '', 'display': '단축키 입력', 'mode': 'left_half'}
            },
            'settings': {'gap': 5}
        }
        res = self.client.post('/api/config',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        saved = mock_save.call_args[0][0]
        self.assertEqual(saved['shortcuts']['Left']['pynput'], '')

    @patch('core.config_manager.save_config')
    def test_gap_setting_persistence(self, mock_save):
        """Gap 설정 변경이 정상 저장되는지 확인"""
        payload = {
            'shortcuts': {},
            'settings': {'gap': 15}
        }
        res = self.client.post('/api/config',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        saved = mock_save.call_args[0][0]
        self.assertEqual(saved['settings']['gap'], 15)

    @patch('core.config_manager.save_config')
    def test_clear_all_hotkeys(self, mock_save):
        """전체 단축키 초기화 후 저장이 정상 처리되는지 확인"""
        shortcuts = {
            'Left': {'pynput': '', 'display': '단축키 입력', 'mode': 'left_half'},
            'Right': {'pynput': '', 'display': '단축키 입력', 'mode': 'right_half'},
        }
        payload = {'shortcuts': shortcuts, 'settings': {'gap': 5}}
        res = self.client.post('/api/config',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        saved = mock_save.call_args[0][0]
        for name, info in saved['shortcuts'].items():
            self.assertEqual(info['pynput'], '')

    def test_config_api_returns_all_shortcut_keys(self):
        """GET /api/config 응답에 기본 단축키 항목이 모두 포함되는지 확인"""
        res = self.client.get('/api/config')
        data = json.loads(res.data)
        expected_keys = ['Left', 'Right', 'Top', 'Bottom']
        for key in expected_keys:
            self.assertIn(key, data['shortcuts'])

    def test_settings_page_renders(self):
        """GET / 설정 페이지가 단축키 목록 관련 HTML을 포함하는지 확인"""
        res = self.client.get('/')
        html = res.data.decode('utf-8')
        self.assertIn('WinResizer', html)
        self.assertIn('api/config', html)


if __name__ == '__main__':
    unittest.main()
