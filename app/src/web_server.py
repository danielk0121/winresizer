import threading
import webbrowser
import socket
import random
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
        .custom-row { display: flex; align-items: center; gap: 8px; margin-bottom: 8px; flex-wrap: wrap; }
        .custom-label { width: 80px; font-size: 14px; color: #ccc; flex-shrink: 0; }
        .pct-input {
            width: 70px; padding: 6px 10px; background: #3a3a3a; border: 1px solid #555;
            border-radius: 6px; color: #fff; font-size: 14px;
        }
        .apply-btn {
            padding: 6px 16px; background: #27ae60; border: none; border-radius: 6px;
            color: #fff; font-size: 14px; cursor: pointer; font-weight: bold;
        }
        .apply-btn:hover { background: #2ecc71; }
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

    <div class="section">
        <div class="section-title">커스텀 비율 창 조절</div>
        <div style="font-size:12px; color:#666; margin-bottom:10px;">비율(1~99%)을 입력하고 단축키를 설정하세요. 적용 버튼으로 즉시 실행도 가능합니다.</div>
        <div class="custom-row">
            <span class="custom-label">좌측</span>
            <input class="pct-input" id="pct-left" type="number" min="1" max="99" value="75" placeholder="1~99">
            <span style="color:#aaa; font-size:14px;">%</span>
            <button class="hotkey-btn" id="btn-Left Custom" style="flex:1;" onclick="startRecording('Left Custom')">단축키 입력</button>
            <button class="delete-btn" onclick="deleteHotkey('Left Custom')">✕</button>
            <button class="apply-btn" onclick="applyCustomDirect('left', 'pct-left')">적용</button>
        </div>
        <div class="custom-row">
            <span class="custom-label">우측</span>
            <input class="pct-input" id="pct-right" type="number" min="1" max="99" value="75" placeholder="1~99">
            <span style="color:#aaa; font-size:14px;">%</span>
            <button class="hotkey-btn" id="btn-Right Custom" style="flex:1;" onclick="startRecording('Right Custom')">단축키 입력</button>
            <button class="delete-btn" onclick="deleteHotkey('Right Custom')">✕</button>
            <button class="apply-btn" onclick="applyCustomDirect('right', 'pct-right')">적용</button>
        </div>
        <div class="custom-row">
            <span class="custom-label">상단</span>
            <input class="pct-input" id="pct-top" type="number" min="1" max="99" value="75" placeholder="1~99">
            <span style="color:#aaa; font-size:14px;">%</span>
            <button class="hotkey-btn" id="btn-Top Custom" style="flex:1;" onclick="startRecording('Top Custom')">단축키 입력</button>
            <button class="delete-btn" onclick="deleteHotkey('Top Custom')">✕</button>
            <button class="apply-btn" onclick="applyCustomDirect('top', 'pct-top')">적용</button>
        </div>
        <div class="custom-row">
            <span class="custom-label">하단</span>
            <input class="pct-input" id="pct-bottom" type="number" min="1" max="99" value="75" placeholder="1~99">
            <span style="color:#aaa; font-size:14px;">%</span>
            <button class="hotkey-btn" id="btn-Bottom Custom" style="flex:1;" onclick="startRecording('Bottom Custom')">단축키 입력</button>
            <button class="delete-btn" onclick="deleteHotkey('Bottom Custom')">✕</button>
            <button class="apply-btn" onclick="applyCustomDirect('bottom', 'pct-bottom')">적용</button>
        </div>
    </div>

    <button class="save-btn" onclick="saveConfig()">저장 및 적용</button>
    <button class="clear-btn" onclick="clearAll()">전체 단축키 초기화</button>
    <div id="status"></div>

    <script>
        let config = {};
        let recordingKey = null;

        // 커스텀 비율 키 목록 (웹 UI 커스텀 섹션에서 별도 렌더링)
        const CUSTOM_KEYS = ['Left Custom', 'Right Custom', 'Top Custom', 'Bottom Custom'];
        // 커스텀 키와 비율 입력 id 매핑
        const CUSTOM_PCT_IDS = {
            'Left Custom': 'pct-left',
            'Right Custom': 'pct-right',
            'Top Custom': 'pct-top',
            'Bottom Custom': 'pct-bottom',
        };

        async function loadConfig() {
            const res = await fetch('/api/config');
            config = await res.json();
            document.getElementById('gap').value = config.settings?.gap ?? 5;
            renderHotkeys();
            renderCustomHotkeys();
        }

        function renderHotkeys() {
            const list = document.getElementById('hotkey-list');
            list.innerHTML = '';
            for (const [name, info] of Object.entries(config.shortcuts || {})) {
                // 커스텀 비율 키는 커스텀 섹션에서 별도 렌더링
                if (CUSTOM_KEYS.includes(name)) continue;
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

        function renderCustomHotkeys() {
            // 커스텀 비율 키의 단축키 표시 및 비율값 반영
            for (const name of CUSTOM_KEYS) {
                const info = config.shortcuts?.[name];
                if (!info) continue;
                const btn = document.getElementById('btn-' + name);
                if (btn) btn.textContent = info.display || '단축키 입력';
                // mode에서 비율값 추출해 입력창에 반영
                const pctId = CUSTOM_PCT_IDS[name];
                const mode = info.mode || '';
                const match = mode.match(/_custom:(\\d+)$/);
                if (match && pctId) {
                    document.getElementById(pctId).value = match[1];
                }
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

            // 커스텀 비율 mode를 현재 입력값으로 갱신
            const dirMap = {
                'Left Custom': 'left',
                'Right Custom': 'right',
                'Top Custom': 'top',
                'Bottom Custom': 'bottom',
            };
            for (const [name, dir] of Object.entries(dirMap)) {
                const pctId = CUSTOM_PCT_IDS[name];
                const pct = parseInt(document.getElementById(pctId).value);
                if (!isNaN(pct) && pct >= 1 && pct <= 99) {
                    if (config.shortcuts[name]) {
                        config.shortcuts[name].mode = `${dir}_custom:${pct}`;
                    }
                }
            }

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

        async function applyCustomDirect(direction, pctInputId) {
            const pct = parseInt(document.getElementById(pctInputId).value);
            const status = document.getElementById('status');
            if (isNaN(pct) || pct < 1 || pct > 99) {
                status.style.color = '#e74c3c';
                status.textContent = '비율은 1~99 사이 정수를 입력하세요.';
                setTimeout(() => { status.textContent = ''; status.style.color = '#2ecc71'; }, 3000);
                return;
            }
            const mode = `${direction}_custom:${pct}`;
            const res = await fetch('/api/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });
            if (res.ok) {
                status.style.color = '#2ecc71';
                status.textContent = `${direction} ${pct}% 적용 완료`;
            } else {
                status.style.color = '#e74c3c';
                status.textContent = '적용 실패';
            }
            setTimeout(() => { status.textContent = ''; status.style.color = '#2ecc71'; }, 2000);
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
    app.config['listener'] = listener

    server_thread = threading.Thread(
        target=lambda: app.run(host='127.0.0.1', port=port, debug=False, use_reloader=False),
        daemon=True
    )
    server_thread.start()
    logger.info(f"웹 서버 시작: http://127.0.0.1:{port}")

    # 실행 포트를 설정 파일에 기록
    from core import config_manager
    config_manager.save_server_port(port)

    return app, port


def open_browser(port):
    webbrowser.open(f'http://127.0.0.1:{port}')
