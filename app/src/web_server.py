import threading
import webbrowser
from flask import Flask, jsonify, request, render_template_string
from core import config_manager
from core.hotkey_listener import HotkeyListenerThread
from utils.logger import logger

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WinResizer 설정</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: #2b2b2b; color: #fff; font-family: -apple-system, sans-serif; padding: 24px; }
        h1 { font-size: 20px; margin-bottom: 20px; color: #eee; }
        .section { margin-bottom: 24px; }
        .section-title { font-size: 13px; color: #888; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
        .row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
        .label { width: 140px; font-size: 14px; color: #ccc; flex-shrink: 0; }
        .hotkey-btn {
            flex: 1; padding: 7px 12px; background: #3a3a3a; border: 1px solid #555;
            border-radius: 6px; color: #fff; cursor: pointer; font-size: 13px; text-align: left;
        }
        .hotkey-btn.recording { border-color: #f39c12; background: #3d3520; color: #f39c12; }
        .delete-btn {
            width: 28px; height: 28px; background: #444; border: none; border-radius: 4px;
            color: #bbb; cursor: pointer; font-size: 14px; flex-shrink: 0;
        }
        .delete-btn:hover { background: #e74c3c; color: #fff; }
        .gap-row { display: flex; align-items: center; gap: 10px; }
        .gap-input {
            width: 70px; padding: 6px 10px; background: #3a3a3a; border: 1px solid #555;
            border-radius: 6px; color: #fff; font-size: 14px;
        }
        .save-btn {
            margin-top: 24px; width: 100%; padding: 12px; background: #2980b9;
            border: none; border-radius: 8px; color: #fff; font-size: 15px;
            font-weight: bold; cursor: pointer;
        }
        .save-btn:hover { background: #3498db; }
        .clear-btn {
            margin-top: 10px; width: 100%; padding: 10px; background: #c0392b;
            border: none; border-radius: 8px; color: #fff; font-size: 14px; cursor: pointer;
        }
        .clear-btn:hover { background: #e74c3c; }
        #status { margin-top: 12px; text-align: center; font-size: 13px; color: #2ecc71; height: 20px; }
    </style>
</head>
<body>
    <h1>WinResizer 설정</h1>

    <div class="section">
        <div class="section-title">창 간격 (Gap)</div>
        <div class="gap-row">
            <label class="label">Gap (px)</label>
            <input class="gap-input" id="gap" type="number" min="0" max="50" value="5">
        </div>
    </div>

    <div class="section">
        <div class="section-title">단축키</div>
        <div id="hotkey-list"></div>
    </div>

    <button class="save-btn" onclick="saveConfig()">저장 및 적용</button>
    <button class="clear-btn" onclick="clearAll()">전체 단축키 초기화</button>
    <div id="status"></div>

    <script>
        let config = {};
        let recordingKey = null;

        async function loadConfig() {
            const res = await fetch('/api/config');
            config = await res.json();
            document.getElementById('gap').value = config.settings?.gap ?? 5;
            renderHotkeys();
        }

        function renderHotkeys() {
            const list = document.getElementById('hotkey-list');
            list.innerHTML = '';
            for (const [name, info] of Object.entries(config.shortcuts || {})) {
                const row = document.createElement('div');
                row.className = 'row';
                row.innerHTML = `
                    <span class="label">${name}</span>
                    <button class="hotkey-btn" id="btn-${name}" onclick="startRecording('${name}')">${info.display || '단축키 입력'}</button>
                    <button class="delete-btn" onclick="deleteHotkey('${name}')">✕</button>
                `;
                list.appendChild(row);
            }
        }

        function startRecording(keyName) {
            if (recordingKey) stopRecording();
            recordingKey = keyName;
            const btn = document.getElementById('btn-' + keyName);
            btn.textContent = '키 입력 대기...';
            btn.classList.add('recording');
        }

        function stopRecording() {
            if (!recordingKey) return;
            const btn = document.getElementById('btn-' + recordingKey);
            if (btn) btn.classList.remove('recording');
            recordingKey = null;
        }

        document.addEventListener('keydown', (e) => {
            if (!recordingKey) return;
            e.preventDefault();

            // Backspace / Delete → 단축키 삭제
            if (e.key === 'Backspace' || e.key === 'Delete') {
                config.shortcuts[recordingKey].pynput = '';
                config.shortcuts[recordingKey].display = '단축키 입력';
                document.getElementById('btn-' + recordingKey).textContent = '단축키 입력';
                stopRecording();
                return;
            }

            // 수정자 키만 누른 경우 무시
            if (['Control', 'Alt', 'Meta', 'Shift'].includes(e.key)) return;

            const parts = [];
            if (e.ctrlKey) parts.push('<ctrl>');
            if (e.altKey) parts.push('<alt>');
            if (e.metaKey) parts.push('<cmd>');
            if (e.shiftKey) parts.push('<shift>');

            const key = e.key.length === 1 ? e.key.toLowerCase() : `<${e.key.toLowerCase()}>`;
            parts.push(key);

            const pynput = parts.join('+');
            const display = pynput.replace(/[<>]/g, '').replace(/\\+/g, ' + ');

            config.shortcuts[recordingKey].pynput = pynput;
            config.shortcuts[recordingKey].display = display;
            document.getElementById('btn-' + recordingKey).textContent = display;
            stopRecording();
        });

        function deleteHotkey(keyName) {
            config.shortcuts[keyName].pynput = '';
            config.shortcuts[keyName].display = '단축키 입력';
            renderHotkeys();
        }

        function clearAll() {
            if (!confirm('전체 단축키를 초기화할까요?')) return;
            for (const name of Object.keys(config.shortcuts || {})) {
                config.shortcuts[name].pynput = '';
                config.shortcuts[name].display = '단축키 입력';
            }
            renderHotkeys();
        }

        async function saveConfig() {
            config.settings = config.settings || {};
            config.settings.gap = parseInt(document.getElementById('gap').value) || 0;

            const res = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            const status = document.getElementById('status');
            if (res.ok) {
                status.textContent = '저장 완료! 단축키가 즉시 반영되었습니다.';
            } else {
                status.textContent = '저장 실패.';
            }
            setTimeout(() => status.textContent = '', 3000);
        }

        loadConfig();
    </script>
</body>
</html>
"""


def create_app():
    """Flask 앱 팩토리"""
    app = Flask(__name__)
    app.config['listener'] = None

    @app.route('/')
    def index():
        return render_template_string(HTML_TEMPLATE)

    @app.route('/api/config', methods=['GET'])
    def get_config():
        return jsonify(config_manager.load_config())

    @app.route('/api/config', methods=['POST'])
    def post_config():
        data = request.get_json(silent=True)
        if data is None:
            return jsonify({'error': '잘못된 요청입니다.'}), 400

        config_manager.save_config(data)
        config_manager._config_cache = None  # 캐시 초기화

        # 리스너 재시작
        listener = app.config.get('listener')
        if listener is not None:
            listener.stop()
            new_listener = HotkeyListenerThread()
            new_listener.start()
            app.config['listener'] = new_listener

        logger.info("설정 저장 및 리스너 재시작 완료")
        return jsonify({'status': 'ok'})

    return app


def run_server(port=5000, listener=None):
    """Flask 서버를 백그라운드 스레드로 실행"""
    app = create_app()
    app.config['listener'] = listener

    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    logger.info(f"웹 서버 시작: http://127.0.0.1:{port}")
    return app


def open_browser(port=5000):
    webbrowser.open(f'http://127.0.0.1:{port}')
