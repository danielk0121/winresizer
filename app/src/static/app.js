// ── 언어 설정 ──────────────────────────────────────────────────
const LANG = {
    ko: {
        title:        'WinResizer 설정',
        saveBtn:      '저장 및 적용',
        clearBtn:     '전체 단축키 초기화',
        saveDone:     '저장 완료! 단축키가 즉시 반영되었습니다.',
        saveFail:     '저장 실패.',
        customSection:'커스텀 비율 창 조절',
        customDesc:   '비율(1~99%)을 입력하고 단축키를 설정하세요. 적용 버튼으로 즉시 실행도 가능합니다.',
        dirLeft:      '좌측',
        dirRight:     '우측',
        dirTop:       '상단',
        dirBottom:    '하단',
        hotkeySection:'단축키',
        hotkeyDefault:'단축키 입력',
        hotkeyWaiting:'키 입력 대기...',
        gapSection:   '창 간격 (Gap)',
        confirmClear: '전체 단축키를 초기화할까요?',
        pctError:     '비율은 1~99 사이 정수를 입력하세요.',
        applyDone:    (dir, pct) => `${dir} ${pct}% 적용 완료`,
        applyFail:    '적용 실패',
    },
    en: {
        title:        'WinResizer Settings',
        saveBtn:      'Save & Apply',
        clearBtn:     'Reset All Hotkeys',
        saveDone:     'Saved! Hotkeys applied immediately.',
        saveFail:     'Save failed.',
        customSection:'Custom Ratio Resize',
        customDesc:   'Enter a ratio (1~99%) and set a hotkey. Use the Apply button to resize immediately.',
        dirLeft:      'Left',
        dirRight:     'Right',
        dirTop:       'Top',
        dirBottom:    'Bottom',
        hotkeySection:'Hotkeys',
        hotkeyDefault:'Press hotkey',
        hotkeyWaiting:'Waiting for key...',
        gapSection:   'Window Gap',
        confirmClear: 'Reset all hotkeys?',
        pctError:     'Enter an integer between 1 and 99.',
        applyDone:    (dir, pct) => `${dir} ${pct}% applied`,
        applyFail:    'Apply failed',
    },
};

let currentLang = localStorage.getItem('lang') || 'ko';

function t(key, ...args) {
    const val = LANG[currentLang][key];
    return typeof val === 'function' ? val(...args) : val;
}

function setLang(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    applyLang();
    // 단축키 버튼 텍스트 갱신 (녹화 중이 아닌 버튼만)
    renderHotkeys();
    renderCustomHotkeys();
}

function applyLang() {
    // data-i18n 속성 요소 텍스트 일괄 교체
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (LANG[currentLang][key] !== undefined) {
            el.textContent = t(key);
        }
    });
    // 언어 버튼 활성화 표시
    document.getElementById('lang-ko').classList.toggle('active', currentLang === 'ko');
    document.getElementById('lang-en').classList.toggle('active', currentLang === 'en');
    // html lang 속성 갱신
    document.documentElement.lang = currentLang;
}

// ── 커스텀 비율 키 설정 ────────────────────────────────────────
const CUSTOM_KEYS = ['Left Custom', 'Right Custom', 'Top Custom', 'Bottom Custom'];

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
    applyLang();
    renderHotkeys();
    renderCustomHotkeys();
}

function renderHotkeys() {
    const list = document.getElementById('hotkey-list');
    list.innerHTML = '';
    const shortcuts = config.shortcuts || {};
    for (const name of HOTKEY_ORDER) {
        const info = shortcuts[name];
        if (!info) continue;
        const display = info.pynput ? info.display : t('hotkeyDefault');
        const row = document.createElement('div');
        row.className = 'row';
        row.innerHTML = `
            <span class="label">${name}</span>
            <button class="hotkey-btn" id="btn-${name}" onclick="startRecording('${name}')">${display}</button>
            <button class="delete-btn" onclick="deleteHotkey('${name}')">✕</button>
        `;
        list.appendChild(row);
    }
}

function renderCustomHotkeys() {
    for (const name of CUSTOM_KEYS) {
        const info = config.shortcuts?.[name];
        if (!info) continue;
        const btn = document.getElementById('btn-' + name);
        if (btn && !btn.classList.contains('recording')) {
            btn.textContent = info.pynput ? info.display : t('hotkeyDefault');
        }
        const pctId = CUSTOM_PCT_IDS[name];
        const mode = info.mode || '';
        const match = mode.match(/_custom:(\d+)$/);
        if (match && pctId) {
            document.getElementById(pctId).value = match[1];
        }
    }
}

function startRecording(keyName) {
    if (recordingKey) stopRecording();
    recordingKey = keyName;
    const btn = document.getElementById('btn-' + keyName);
    btn.textContent = t('hotkeyWaiting');
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

    if (e.key === 'Backspace' || e.key === 'Delete') {
        config.shortcuts[recordingKey].pynput = '';
        config.shortcuts[recordingKey].display = '';
        document.getElementById('btn-' + recordingKey).textContent = t('hotkeyDefault');
        stopRecording();
        return;
    }

    if (['Control', 'Alt', 'Meta', 'Shift'].includes(e.key)) return;

    // 브라우저 e.key → pynput 키 이름 변환 맵
    const KEY_MAP = {
        'arrowleft':  'left',
        'arrowright': 'right',
        'arrowup':    'up',
        'arrowdown':  'down',
        'enter':      'enter',
        'escape':     'esc',
        'tab':        'tab',
        'space':      'space',
        ' ':          'space',
    };

    const parts = [];
    if (e.ctrlKey)  parts.push('<ctrl>');
    if (e.altKey)   parts.push('<alt>');
    if (e.metaKey)  parts.push('<cmd>');
    if (e.shiftKey) parts.push('<shift>');

    const rawKey = e.key.toLowerCase();
    const mappedKey = KEY_MAP[rawKey] || rawKey;
    const key = mappedKey.length === 1 ? mappedKey : `<${mappedKey}>`;
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
    config.shortcuts[keyName].display = '';
    renderHotkeys();
    renderCustomHotkeys();
}

function clearAll() {
    if (!confirm(t('confirmClear'))) return;
    for (const name of Object.keys(config.shortcuts || {})) {
        config.shortcuts[name].pynput = '';
        config.shortcuts[name].display = '';
    }
    renderHotkeys();
    renderCustomHotkeys();
}

async function saveConfig() {
    config.settings = config.settings || {};
    config.settings.gap = parseInt(document.getElementById('gap').value) || 0;

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
        status.style.color = '#2ecc71';
        status.textContent = t('saveDone');
    } else {
        status.style.color = '#e74c3c';
        status.textContent = t('saveFail');
    }
    setTimeout(() => { status.textContent = ''; status.style.color = '#2ecc71'; }, 3000);
}

loadConfig();
