import json
import os
import sys as _sys
from utils.logger import logger

from utils.helpers import get_resource_path

# 사용자 설정 파일 경로 (~/Library/Application Support/WinResizer/config.json)
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "WinResizer", "config.json")

# 개발 환경 대응: 로컬에 config.json이 있으면 우선 사용 (테스트용)
_LOCAL_DEV_CONFIG = get_resource_path("app/src/config/config.json")
if not getattr(_sys, 'frozen', False) and os.path.exists(_LOCAL_DEV_CONFIG):
    CONFIG_FILE = _LOCAL_DEV_CONFIG

# 기본 설정 파일 (번들에 포함된 원본)
DEFAULT_CONFIG_FILE = get_resource_path("app/src/config/default-config.json")

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


def save_runtime_info(port):
    """런타임 정보(포트, PID, 시작 시간)를 기록합니다."""
    import os as _os
    from datetime import datetime, timedelta, timezone
    
    ensure_config_dir()
    try:
        data = {}
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        
        # KST (UTC+9) 시간 계산 (ISO 8601 형식)
        kst = timezone(timedelta(hours=9))
        now_kst = datetime.now(kst).isoformat(timespec='seconds')
        
        data.setdefault('runtime', {})
        data['runtime'].update({
            'port': port,
            'pid': _os.getpid(),
            'start_time': now_kst
        })
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.debug(f"런타임 정보 기록 완료: PID={_os.getpid()}, Port={port}")
    except Exception as e:
        logger.error(f"런타임 정보 기록 중 오류 발생: {e}")
