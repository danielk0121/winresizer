import sys
import socket
from core.window_controller import execute_window_command
from utils.logger import logger

def run_network_command_server():
    """
    Server that processes only window control commands via network, without hotkey listeners.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Listen on all interfaces (0.0.0.0)
            s.bind(('0.0.0.0', 9999))
            s.listen()
            logger.info("Network control server started (Port: 9999)")
            while True:
                conn, addr = s.accept()
                with conn:
                    data = conn.recv(1024).decode().strip()
                    if data:
                        logger.info(f"[Remote command received] {data} (From: {addr})")
                        execute_window_command(data)
    except KeyboardInterrupt:
        logger.info("Stopping server.")
    except Exception as e:
        logger.error(f"Error while running server: {e}")

if __name__ == "__main__":
    run_network_command_server()
