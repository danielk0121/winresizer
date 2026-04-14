// 커스텀 비율 키 목록 (웹 UI 커스텀 섹션에서 별도 렌더링)
const CUSTOM_KEYS = ['Left Custom', 'Right Custom', 'Top Custom', 'Bottom Custom'];

// 커스텀 키와 비율 입력 id 매핑
const CUSTOM_PCT_IDS = {
    'Left Custom': 'pct-left',
    'Right Custom': 'pct-right',
    'Top Custom': 'pct-top',
    'Bottom Custom': 'pct-bottom',
};

// 단축키 섹션 렌더링 순서
const HOTKEY_ORDER = [
    'Left', 'Right', 'Top', 'Bottom',
    'Left 1/3', 'Center 1/3', 'Right 1/3',
    'Left 2/3', 'Right 2/3',
    'Top Left 1/4', 'Top Right 1/4', 'Bottom Left 1/4', 'Bottom Right 1/4',
    'Maximize', 'Restore',
];

let config = {};
let recordingKey = null;

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
    // HOTKEY_ORDER 기준 고정 순서 렌더링
    const shortcuts = config.shortcuts || {};
    for (const name of HOTKEY_ORDER) {
        const info = shortcuts[name];
        if (!info) continue;
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
    const display = pynput.replace(/[<>]/g, '').replace(/\+/g, ' + ');

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
