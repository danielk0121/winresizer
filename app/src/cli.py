import sys
import socket
import threading
from pynput import keyboard
from core.window_controller import execute_window_command
from utils.logger import logger

def start_socket_server():
    """
    Start a socket server to receive external commands (CLI, etc.).
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('127.0.0.1', 9999))
        s.listen()
        logger.info("CLI socket server started (127.0.0.1:9999)")
        while True:
            conn, _ = s.accept()
            with conn:
                data = conn.recv(1024).decode().strip()
                if data:
                    logger.info(f"[Socket command received] {data}")
                    execute_window_command(data)

if __name__ == "__main__":
    # Start socket server in a separate thread
    threading.Thread(target=start_socket_server, daemon=True).start()
    
    logger.info("CLI WinResizer listener running...")
    
    # Default hotkey settings (fixed hotkeys for CLI mode)
    hotkey_map = {
        '<ctrl>+<alt>+<cmd>+<left>': lambda: execute_window_command('좌측_절반'),
        '<ctrl>+<alt>+<cmd>+<right>': lambda: execute_window_command('우측_절반'),
        '<ctrl>+<alt>+<cmd>+<up>': lambda: execute_window_command('다음_디스플레이'),
        '<ctrl>+<alt>+<cmd>+r': lambda: execute_window_command('복구')
    }
    
    with keyboard.GlobalHotKeys(hotkey_map) as h:
        h.join()
