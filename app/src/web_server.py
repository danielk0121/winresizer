import threading
import webbrowser
import socket
import random
import os
import sys
from flask import Flask, jsonify, request, render_template
from core import config_manager
from utils.logger import logger

from utils.helpers import get_resource_path


def create_app():
    """Flask 앱 팩토리"""
    app = Flask(
        __name__,
        template_folder=get_resource_path('app/src/templates'),
        static_folder=get_resource_path('app/src/static'),
    )

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/status', methods=['GET'])
    def get_status():
        """
        현재 애플리케이션의 상태(권한 등)를 반환합니다.
        """
        from core.window_manager import is_accessibility_trusted, is_input_monitoring_trusted
        return jsonify({
            "accessibility_granted": is_accessibility_trusted(),
            "input_monitoring_granted": is_input_monitoring_trusted(),
            "pid": os.getpid()
        })

    @app.route('/api/config', methods=['GET'])
    def get_config():
        return jsonify(config_manager.load_config())

    @app.route('/api/execute', methods=['POST'])
    def execute_command():
        """창 조절 명령을 즉시 실행하는 API (E2E 테스트 및 외부 트리거용)"""
        data = request.get_json(silent=True)
        if not data or 'mode' not in data:
            return jsonify({'error': 'mode 필드가 필요합니다.'}), 400
        from core.window_controller import execute_window_command
        execute_window_command(data['mode'])
        return jsonify({'status': 'ok', 'mode': data['mode']})

    @app.route('/api/execute', methods=['GET'])
    def execute_command_get():
        """창 조절 명령 GET 버전 (테스트 편의용)"""
        mode = request.args.get('mode')
        if not mode:
            return jsonify({'error': 'mode 파라미터가 필요합니다.'}), 400
        from core.window_controller import execute_window_command
        execute_window_command(mode)
        return jsonify({'status': 'ok', 'mode': mode})

    @app.route('/api/config/reset', methods=['POST'])
    def reset_config():
        """기본 설정값을 반환합니다. (실제 저장은 하지 않음)"""
        default = config_manager._deep_copy_default()
        # 실제 저장은 사용자가 클라이언트에서 '저장' 버튼을 누를 때 수행됨
        logger.info("기본 설정값 요청됨 (저장 미수행)")
        return jsonify({'status': 'ok', 'config': default})

    @app.route('/api/config', methods=['POST'])
    def post_config():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({'error': '잘못된 요청입니다.'}), 400

        config_manager.save_config(data)
        config_manager._config_cache = None  # 캐시 무효화 — 다음 키 입력 시 리스너가 새 설정 자동 반영
        logger.info("설정 저장 완료")
        return jsonify({'status': 'ok'})

    @app.after_request
    def add_header(response):
        """브라우저 캐시 방지 헤더 추가"""
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        # response.headers['Pragma'] = 'no-cache'  # Pragma는 Flask-Internal에서 처리 가능
        response.headers['Expires'] = '0'
        return response

    return app


def find_free_port(start=40000, end=49999):
    """40000–49999 범위에서 사용 가능한 랜덤 포트 반환"""
    while True:
        port = random.randint(start, end)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port


def run_server(port=None, listener=None):
    """Flask 서버를 백그라운드 스레드로 실행. port=None 이면 40000번대 랜덤 포트 사용."""
    if port is None:
        port = find_free_port()

    app = create_app()

    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    logger.info(f"웹 서버 시작: http://127.0.0.1:{port}")

    # 실행 포트를 설정 파일에 기록
    from core import config_manager
    config_manager.save_runtime_info(port)

    return app, port


def open_browser(port):
    webbrowser.open(f'http://127.0.0.1:{port}')
