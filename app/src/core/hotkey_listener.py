from utils.logger import logger
import time
import threading
from pynput import keyboard
from core.window_manager import is_accessibility_trusted
from core.window_controller import execute_window_command
from core import config_manager

# Status flag for hotkey recording (shared with GUI)
RECORDING_STATUS = {'is_recording': False}

class HotkeyListenerThread(threading.Thread):
    """
    Background thread that detects global hotkeys.
    """
    def __init__(self):
        super().__init__()
        self.daemon = True
        self._stop_event = threading.Event()
        self._kb_listener = None  # keyboard.Listener 직접 참조 보관

    def stop(self):
        self._stop_event.set()
        # keyboard.Listener(CGEventTap)를 직접 중단하여 즉시 해제
        if self._kb_listener is not None:
            try:
                self._kb_listener.stop()
            except Exception:
                pass
        # 스레드가 완전히 종료될 때까지 최대 2초 대기
        self.join(timeout=2.0)

    def run(self):
        logger.info("Starting hotkey listener thread")
        if not is_accessibility_trusted():
            logger.warning("Cannot start listener without Accessibility permissions.")
            return
        
        currently_pressed_keys = set()
        last_trigger_time = 0

        def on_press(key):
            nonlocal last_trigger_time
            
            # Ignore listener actions if recording
            if RECORDING_STATUS['is_recording']:
                return
                
            try:
                # Extract key name
                k = key.char.lower() if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
                currently_pressed_keys.add(k)
                
                current_time = time.time()
                config = config_manager.get_config()
                hotkey_config = config.get('shortcuts', {})
                
                # custom 모드를 일반 모드보다 먼저 검사 (동일 키 조합 충돌 방지)
                sorted_configs = sorted(
                    hotkey_config.values(),
                    key=lambda c: 0 if '_custom:' in c.get('mode', '') else 1
                )
                for cfg in sorted_configs:
                    pynput_str = cfg.get('pynput')
                    if not pynput_str:
                        continue

                    required_keys = set(pynput_str.replace('<', '').replace('>', '').split('+'))
                    if required_keys.issubset(currently_pressed_keys):
                        # Apply cooldown (0.2s)
                        if current_time - last_trigger_time > 0.2:
                            logger.debug(f"Hotkey detected: {pynput_str}")
                            execute_window_command(cfg['mode'])
                            last_trigger_time = current_time
                        
                        # Support continuous input by keeping only modifier keys in the set
                        modifier_keys = {
                            'ctrl', 'alt', 'cmd', 'shift', 
                            'ctrl_l', 'ctrl_r', 'alt_l', 'alt_r', 
                            'cmd_l', 'cmd_r', 'shift_l', 'shift_r'
                        }
                        currently_pressed_keys.intersection_update(modifier_keys)
                        break
            except Exception as e:
                logger.error(f"Error processing hotkey (on_press): {e}")

        def on_release(key):
            try:
                k = key.char.lower() if hasattr(key, 'char') and key.char else str(key).replace('Key.', '')
                if k in currently_pressed_keys:
                    currently_pressed_keys.remove(k)
            except Exception as e:
                logger.error(f"Error processing hotkey (on_release): {e}")

        logger.info("Hotkey engine running")
        try:
            with keyboard.Listener(on_press=on_press, on_release=on_release) as kb_listener:
                self._kb_listener = kb_listener
                while not self._stop_event.is_set():
                    kb_listener.join(timeout=0.5)
                    if not kb_listener.is_alive():
                        break
        except Exception as e:
            logger.error(f"Fatal error in listener: {e}", exc_info=True)
        finally:
            self._kb_listener = None
