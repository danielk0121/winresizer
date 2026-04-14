import unittest
import json
from unittest.mock import patch, MagicMock


class TestWebServer(unittest.TestCase):
    """Flask 웹 서버 API 엔드포인트 검증"""

    def setUp(self):
        from web_server import create_app
        self.app = create_app()
        self.client = self.app.test_client()

    def test_get_index(self):
        """GET / 설정 페이지가 200을 반환하는지 확인"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)

    def test_get_config_api(self):
        """GET /api/config 가 JSON 설정을 반환하는지 확인"""
        res = self.client.get('/api/config')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('shortcuts', data)
        self.assertIn('settings', data)

    @patch('core.config_manager.save_config')
    def test_post_config_api(self, mock_save):
        """POST /api/config 가 설정을 저장하고 200을 반환하는지 확인"""
        payload = {
            'shortcuts': {'Left': {'pynput': '<ctrl>+<left>', 'display': 'ctrl + left', 'mode': 'left_half'}},
            'settings': {'gap': 10}
        }
        res = self.client.post('/api/config',
                               data=json.dumps(payload),
                               content_type='application/json')
        self.assertEqual(res.status_code, 200)
        mock_save.assert_called_once()

    def test_post_config_invalid_json(self):
        """POST /api/config 에 잘못된 JSON 전송 시 400 반환"""
        res = self.client.post('/api/config',
                               data='not-json',
                               content_type='application/json')
        self.assertEqual(res.status_code, 400)


if __name__ == '__main__':
    unittest.main()
