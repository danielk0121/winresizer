import json
import os
import logging

# 현재 파일(config_manager.py)의 위치를 기준으로 절대 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")

def ensure_config_dir():
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

DEFAULT_CONFIG = {
    '왼쪽': {'pynput': '<ctrl>+<alt>+<cmd>+<left>', 'display': '⌃⌥⌘←', 'mode': '좌측_절반'},
    '오른쪽': {'pynput': '<ctrl>+<alt>+<cmd>+<right>', 'display': '⌃⌥⌘→', 'mode': '우측_절반'},
    '위': {'pynput': '<ctrl>+<alt>+<cmd>+<up>', 'display': '⌃⌥⌘↑', 'mode': '위쪽_절반'},
    '아래': {'pynput': '<ctrl>+<alt>+<cmd>+<down>', 'display': '⌃⌥⌘↓', 'mode': '아래쪽_절반'},
    '좌상단 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': '좌상단_1/4'},
    '우상단 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': '우상단_1/4'},
    '좌하단 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': '좌하단_1/4'},
    '우하단 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': '우하단_1/4'},
    '좌측 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '좌측_1/3'},
    '중앙 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '중앙_1/3'},
    '우측 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '우측_1/3'},
    '좌측 2/3': {'pynput': '', 'display': '단축키 입력', 'mode': '좌측_2/3'},
    '우측 2/3': {'pynput': '', 'display': '단축키 입력', 'mode': '우측_2/3'},
    '최대화': {'pynput': '', 'display': '단축키 입력', 'mode': '최대화'},
    '복구': {'pynput': '', 'display': '단축키 입력', 'mode': '복구'},
}

# 기본 시스템 설정 (간격 등)
DEFAULT_SETTINGS = {
    'gap': 5,
    'login_launch': True,
    'auto_layouts': {
        'Slack': '우측_1/3',
        'iTerm2': '좌측_2/3'
    },
    'ignore_apps': ['Photoshop', 'Final Cut Pro', 'Steam']
}

def load_config():
    """파일에서 설정을 불러옵니다. 파일이 없으면 기본값을 반환합니다."""
    # 1. 기본값으로 초기화
    config_data = {
        'shortcuts': DEFAULT_CONFIG.copy(),
        'settings': DEFAULT_SETTINGS.copy()
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                
                # 2. 단축키 설정 로드 (파일에 있는 값 중 유효한 것만 취함)
                loaded_shortcuts = loaded.get('shortcuts', loaded if 'shortcuts' not in loaded else {})
                if isinstance(loaded_shortcuts, dict):
                    for k, v in loaded_shortcuts.items():
                        if k in config_data['shortcuts']:
                            if isinstance(v, dict):
                                config_data['shortcuts'][k].update(v)
                            else:
                                logging.warning(f"단축키 설정 '{k}'의 형식이 올바르지 않습니다.")
                
                # 3. 기타 설정 로드
                loaded_settings = loaded.get('settings', {})
                if isinstance(loaded_settings, dict):
                    for k, v in loaded_settings.items():
                        if k in DEFAULT_SETTINGS:
                            config_data['settings'][k] = v
                
                # 4. 필터링된 결과를 파일에 즉시 반영 (삭제된 항목 영구 제거)
                save_config(config_data)
                
        except Exception as e:
            logging.error(f"설정 파일을 불러오는 중 오류 발생: {e}")
            
    return config_data

def save_config(config):
    """현재 설정을 파일에 저장합니다."""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logging.debug(f"설정 파일 저장 성공: {CONFIG_FILE}")
    except Exception as e:
        logging.error(f"설정 저장 중 오류 발생: {e}")
