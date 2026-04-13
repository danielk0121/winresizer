import json
import os
from utils.logger import logger

# 현재 파일(config_manager.py)의 위치를 기준으로 app/src/config/config.json 절대 경로 설정
# app/src/core/config_manager.py -> app/src/config/config.json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")

def ensure_config_dir():
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)

DEFAULT_CONFIG = {
    'Left': {'pynput': '<ctrl>+<alt>+<cmd>+<left>', 'display': 'ctrl + alt + cmd + left', 'mode': 'left_half'},
    'Right': {'pynput': '<ctrl>+<alt>+<cmd>+<right>', 'display': 'ctrl + alt + cmd + right', 'mode': 'right_half'},
    'Top': {'pynput': '<ctrl>+<alt>+<cmd>+<up>', 'display': 'ctrl + alt + cmd + up', 'mode': 'top_half'},
    'Bottom': {'pynput': '<ctrl>+<alt>+<cmd>+<down>', 'display': 'ctrl + alt + cmd + down', 'mode': 'bottom_half'},
    'Top Left 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': 'top_left_1/4'},
    'Top Right 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': 'top_right_1/4'},
    'Bottom Left 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': 'bottom_left_1/4'},
    'Bottom Right 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': 'bottom_right_1/4'},
    'Left 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': 'left_1/3'},
    'Center 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': 'center_1/3'},
    'Right 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': 'right_1/3'},
    'Left 2/3': {'pynput': '', 'display': '단축키 입력', 'mode': 'left_2/3'},
    'Right 2/3': {'pynput': '', 'display': '단축키 입력', 'mode': 'right_2/3'},
    'Maximize': {'pynput': '', 'display': '단축키 입력', 'mode': 'maximize'},
    'Restore': {'pynput': '', 'display': '단축키 입력', 'mode': 'restore'},
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

_config_cache = None

def load_config():
    """파일에서 설정을 불러옵니다. 파일이 없으면 기본값을 반환합니다."""
    global _config_cache
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
                                # 과거 데이터 마이그레이션: pynput을 기반으로 display 형식을 강제 재조정
                                pk = config_data['shortcuts'][k].get('pynput', '')
                                if pk:
                                    # <ctrl>+<alt>+k -> ctrl + alt + k
                                    config_data['shortcuts'][k]['display'] = pk.replace('<', '').replace('>', '').replace('+', ' + ')
                                else:
                                    config_data['shortcuts'][k]['display'] = "단축키 입력"
                            else:
                                logger.warning(f"단축키 설정 '{k}'의 형식이 올바르지 않습니다.")
                
                # 3. 기타 설정 로드
                loaded_settings = loaded.get('settings', {})
                if isinstance(loaded_settings, dict):
                    for k, v in loaded_settings.items():
                        if k in DEFAULT_SETTINGS:
                            config_data['settings'][k] = v
                
        except Exception as e:
            logger.error(f"설정 파일을 불러오는 중 오류 발생: {e}")
    
    _config_cache = config_data
    return config_data

def get_config():
    """캐시된 설정을 반환하거나, 없으면 새로 불러옵니다."""
    global _config_cache
    if _config_cache is None:
        return load_config()
    return _config_cache

def get_setting(key, default=None):
    """지정된 설정값을 반환합니다. 캐시가 없으면 로드합니다."""
    global _config_cache
    if _config_cache is None:
        load_config()
    return _config_cache.get('settings', {}).get(key, default)

def save_config(config):
    """현재 설정을 파일에 저장합니다."""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logger.debug(f"설정 파일 저장 성공: {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"설정 저장 중 오류 발생: {e}")
