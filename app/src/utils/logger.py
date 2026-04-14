import logging
import os
import sys
import datetime

_initialized = False

def setup_logger():
    """
    애플리케이션 전역 로거를 설정합니다.
    """
    global _initialized
    if _initialized:
        return logging.getLogger("winresizer")

    # .app 번들 실행 시에도 안전하게 사용자 홈 기준 경로 사용
    LOG_DIR = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "WinResizer", "log")
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    log_path = os.path.join(LOG_DIR, "winresizer.log")
    
    # 루트 로거 설정 대신 winresizer 전용 로거 설정
    logger = logging.getLogger("winresizer")
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
        
        # 날짜별 롤링 설정: 매일(D) 자정에 실행, 30일(backupCount) 보관
        from logging.handlers import TimedRotatingFileHandler
        file_handler = TimedRotatingFileHandler(
            log_path, 
            when="midnight", 
            interval=1, 
            backupCount=30, 
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        # 롤링 시 파일명 뒤에 .YYYY-MM-DD 가 붙도록 설정
        file_handler.suffix = "%Y-%m-%d"
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
    _initialized = True
    logger.debug("로깅 설정 완료: %s", log_path)
    return logger

# 미리 정의된 로거 객체
logger = setup_logger()
