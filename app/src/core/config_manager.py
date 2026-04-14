import json
import os
import sys as _sys
from utils.logger import logger

# 사용자 설정 파일 경로 (~/Library/Application Support/WinResizer/config.json)
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "WinResizer", "config.json")

# 기본값 파일 경로 (최초 설치/초기화 시에만 사용)
if getattr(_sys, 'frozen', False):
    _BASE = _sys._MEIPASS
else:
    _BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_CONFIG_FILE = os.path.join(_BASE, "config", "default-config.json")

_config_cache = None


def ensure_config_dir():
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)


def load_default_config():
    """default-config.json을 읽어 반환합니다."""
    try:
        with open(DEFAULT_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"기본 설정 파일 로드 실패: {e}")
        return {'shortcuts': {}, 'settings': {}}


def _deep_copy_default():
    """기본 설정의 복사본을 반환합니다."""
    return load_default_config()


def load_config():
    """
    설정을 불러옵니다.
    1. config.json이 있으면 그것만 사용합니다.
    2. 없으면 default-config.json을 읽어 config.json을 생성하고 반환합니다.
    """
    global _config_cache
    
    # 1. 사용자 설정 파일이 존재하는 경우
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                _config_cache = json.load(f)
            return _config_cache
        except Exception as e:
            logger.error(f"사용자 설정 파일 로드 실패: {e}")

    # 2. 파일이 없는 경우 (최초 실행 등) 기본값으로 초기화
    logger.info("사용자 설정 파일이 없어 기본값으로 초기화합니다.")
    config_data = _deep_copy_default()
    save_config(config_data)
    _config_cache = config_data
    return config_data


def get_config():
    """캐시된 설정을 반환하거나 로드합니다."""
    global _config_cache
    if _config_cache is None:
        return load_config()
    return _config_cache


def get_setting(key, default=None):
    """지정된 설정값을 반환합니다."""
    config = get_config()
    return config.get('settings', {}).get(key, default)


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
    """런타임 포트 정보를 기록합니다."""
    ensure_config_dir()
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data.setdefault('runtime', {})['port'] = port
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"서버 포트 기록 중 오류 발생: {e}")
