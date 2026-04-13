import json
import os

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    '왼쪽': {'pynput': '<alt>+<cmd>+<left>', 'display': '⌥⌘←', 'mode': '좌측_절반'},
    '오른쪽': {'pynput': '<alt>+<cmd>+<right>', 'display': '⌥⌘→', 'mode': '우측_절반'},
    '위': {'pynput': '<alt>+<cmd>+<up>', 'display': '⌥⌘↑', 'mode': '위쪽_절반'},
    '아래': {'pynput': '<alt>+<cmd>+<down>', 'display': '⌥⌘↓', 'mode': '아래쪽_절반'},
    '좌상단 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': '좌상단_1/4'},
    '우상단 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': '우상단_1/4'},
    '좌하단 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': '좌하단_1/4'},
    '우하단 1/4': {'pynput': '', 'display': '단축키 입력', 'mode': '우하단_1/4'},
    '좌측 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '좌측_1/3'},
    '중앙 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '중앙_1/3'},
    '우측 1/3': {'pynput': '', 'display': '단축키 입력', 'mode': '우측_1/3'},
    '좌측 2/3': {'pynput': '', 'display': '단축키 입력', 'mode': '좌측_2/3'},
    '우측 2/3': {'pynput': '', 'display': '단축키 입력', 'mode': '우측_2/3'},
    '중앙': {'pynput': '<alt>+<cmd>+c', 'display': '⌥⌘C', 'mode': '중앙_고정'},
    '최대화': {'pynput': '', 'display': '단축키 입력', 'mode': '최대화'},
    '다음 디스플레이': {'pynput': '', 'display': '단축키 입력', 'mode': '다음_디스플레이'},
    '이전 디스플레이': {'pynput': '', 'display': '단축키 입력', 'mode': '이전_디스플레이'},
    '복구': {'pynput': '', 'display': '단축키 입력', 'mode': '복구'},
}

# 기본 시스템 설정 (간격 등)
DEFAULT_SETTINGS = {
    'gap': 5,
    'login_launch': True,
    'center_size': {'width': 1200, 'height': 800},
    'auto_layouts': {
        'Slack': '우측_1/3',
        'iTerm2': '좌측_2/3'
    },
    'ignore_apps': ['Photoshop', 'Final Cut Pro', 'Steam']
}

def load_config():
    """파일에서 설정을 불러옵니다. 파일이 없으면 기본값을 반환합니다."""
    config_data = {
        'shortcuts': DEFAULT_CONFIG.copy(),
        'settings': DEFAULT_SETTINGS.copy()
    }
    
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # 이전 버전 호환성 처리
                if 'shortcuts' in loaded:
                    config_data['shortcuts'].update(loaded['shortcuts'])
                else:
                    # 구버전 구조인 경우 shortcuts로 간주
                    config_data['shortcuts'].update(loaded)
                
                if 'settings' in loaded:
                    config_data['settings'].update(loaded['settings'])
                return config_data
        except Exception as e:
            print(f"설정 파일을 불러오는 중 오류 발생: {e}")
    return config_data

def save_config(config):
    """현재 설정을 파일에 저장합니다."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"설정 저장 중 오류 발생: {e}")
