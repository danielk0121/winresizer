import json
import os
from utils.logger import logger

# 사용자 설정 파일 경로 (~/Library/Application Support/WinResizer/config.json)
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "WinResizer", "config.json")

# 기본값 파일 경로
# - 일반 실행: app/src/core/config_manager.py → app/src/config/default-config.json
# - PyInstaller 번들: sys._MEIPASS(번들 루트)/config/default-config.json
import sys as _sys
if getattr(_sys, 'frozen', False):
    # .app 번들 실행 시 — PyInstaller가 datas를 _MEIPASS 아래에 풀어놓음
    _BASE = _sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_FILE = os.path.join(_BASE, "config", "default-config.json")

_default_config_cache = None
_config_cache = None


def ensure_config_dir():
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)


def load_default_config():
    """default-config.json을 읽어 반환합니다."""
    global _default_config_cache
    if _default_config_cache is not None:
        return _default_config_cache
    try:
        with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
            _default_config_cache = json.load(f)
        logger.debug(f"기본 설정 파일 로드: {DEFAULT_CONFIG_FILE}")
    except Exception as e:
        logger.error(f"기본 설정 파일 로드 실패: {e}")
        _default_config_cache = {'shortcuts': {}, 'settings': {}}
    return _default_config_cache


def _deep_copy_default():
    """default-config의 깊은 복사본을 반환합니다."""
    default = load_default_config()
    return {
        'shortcuts': {k: dict(v) for k, v in default.get('shortcuts', {}).items()},
        'settings': dict(default.get('settings', {})),
    }


def load_config():
    """사용자 config.json을 읽어 default-config 위에 덮어씌워 반환합니다.
    사용자 파일이 없으면 기본값을 그대로 반환합니다."""
    global _config_cache
    # 1. 기본값으로 초기화
    config_data = _deep_copy_default()
    default_shortcuts = load_default_config().get('shortcuts', {})
    default_settings = load_default_config().get('settings', {})

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            # 2. 단축키 설정 로드 — 사용자 값이 있으면 덮어씀
            loaded_shortcuts = loaded.get('shortcuts', {})
            if isinstance(loaded_shortcuts, dict):
                for k, v in loaded_shortcuts.items():
                    if k not in config_data['shortcuts']:
                        continue
                    if not isinstance(v, dict):
                        logger.warning(f"단축키 설정 '{k}'의 형식이 올바르지 않습니다.")
                        continue
                    user_pynput = v.get('pynput', '')
                    if user_pynput:
                        # 사용자가 직접 설정한 단축키 적용
                        config_data['shortcuts'][k].update(v)
                        config_data['shortcuts'][k]['display'] = user_pynput.replace('<', '').replace('>', '').replace('+', ' + ')
                    else:
                        # pynput이 비어있으면 기본값 단축키 유지, mode는 사용자 값 적용 (비율 등)
                        if 'mode' in v:
                            config_data['shortcuts'][k]['mode'] = v['mode']

            # 3. 기타 설정 로드
            loaded_settings = loaded.get('settings', {})
            if isinstance(loaded_settings, dict):
                for k, v in loaded_settings.items():
                    if k in default_settings:
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
    """현재 설정을 사용자 config.json에 저장합니다."""
    ensure_config_dir()
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        logger.debug(f"설정 파일 저장 성공: {CONFIG_FILE}")
    except Exception as e:
        logger.error(f"설정 저장 중 오류 발생: {e}")


def save_server_port(port):
    """Flask 서버 실행 포트를 설정 파일의 runtime 섹션에 기록합니다."""
    ensure_config_dir()
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.setdefault('runtime', {})['port'] = port
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.debug(f"서버 포트 기록: {port}")
    except Exception as e:
        logger.error(f"서버 포트 기록 중 오류 발생: {e}")
