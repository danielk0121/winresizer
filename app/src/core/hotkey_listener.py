from utils.logger import logger
import time
from PyQt5.QtCore import QThread
from pynput import keyboard
from core.window_manager import is_accessibility_trusted
from core.window_controller import execute_window_command
from core import config_manager

# Status flag for hotkey recording (shared with GUI)
RECORDING_STATUS = {'is_recording': False}

class HotkeyListenerThread(QThread):
    """
    Background thread that detects global hotkeys.
    """
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
                config = config_manager.load_config()
                hotkey_config = config.get('shortcuts', {})
                
                for cfg in hotkey_config.values():
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
            with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
                listener.join()
        except Exception as e:
            logger.error(f"Fatal error in listener: {e}", exc_info=True)
