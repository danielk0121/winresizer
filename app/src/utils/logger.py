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

    LOG_DIR = "log"
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    kst_now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"winresizer_{kst_now}_KST.log"
    
    log_path = os.path.join(LOG_DIR, log_filename)
    
    # 루트 로거 설정 대신 winresizer 전용 로거 설정
    logger = logging.getLogger("winresizer")
    logger.setLevel(logging.DEBUG)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s')
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
    _initialized = True
    logger.debug("로깅 설정 완료: %s", log_path)
    return logger

# 미리 정의된 로거 객체
logger = setup_logger()
