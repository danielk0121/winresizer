import sys
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, pyqtSignal
from core.hotkey_listener import RECORDING_STATUS
from core import config_manager
from utils.logger import logger

class HotkeyButton(QPushButton):
    """
    Button widget that provides a recording mode for hotkey input.
    """
    hotkeyChanged = pyqtSignal(str, str)

    def __init__(self, text, key):
        super().__init__(text)
        self.key = key
        self.is_recording = False
        self.clicked.connect(self.start_recording)
        
    def start_recording(self):
        logger.debug(f"Hotkey recording started: {self.key}")
        self.is_recording = True
        RECORDING_STATUS['is_recording'] = True
        self.setText("입력 대기...")
        self.grabKeyboard()
        
    def keyPressEvent(self, event):
        if not self.is_recording:
            super().keyPressEvent(event)
            return
            
        # Cancel (Escape)
        if event.key() == Qt.Key_Escape:
            logger.debug("Hotkey recording cancelled (Escape)")
            self.stop_recording()
            config = config_manager.load_config()
            self.setText(config['shortcuts'][self.key].get('display', "Press hotkey"))
            return
            
        # Delete (Backspace/Delete)
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            logger.debug(f"Hotkey deletion requested: {self.key}")
            self.hotkeyChanged.emit(self.key, "")
            self.setText("Press hotkey")
            self.stop_recording()
            return
        
        # Modifier and normal key combination creation
        parts, d_parts = [], []
        mods = event.modifiers()
        
        # macOS Modifier compensation (considering PyQt5 characteristics)
        if sys.platform == 'darwin':
            if mods & Qt.ControlModifier: 
                parts.append('<cmd>')
                d_parts.append('⌘')
            if mods & Qt.MetaModifier: 
                parts.append('<ctrl>')
                d_parts.append('⌃')
        else:
            if mods & Qt.ControlModifier: 
                parts.append('<ctrl>')
                d_parts.append('⌃')
            if mods & Qt.MetaModifier: 
                parts.append('<cmd>')
                d_parts.append('⌘')

        if mods & Qt.AltModifier: 
            parts.append('<alt>')
            d_parts.append('⌥')
        
        if mods & Qt.ShiftModifier:
            parts.append('<shift>')
            d_parts.append('⇧')
        
        k = event.key()
        # Special key mapping
        kn = {
            Qt.Key_Left: 'left', 
            Qt.Key_Right: 'right', 
            Qt.Key_Up: 'up', 
            Qt.Key_Down: 'down'
        }.get(k, chr(k).lower() if 32 <= k <= 126 else None)
        
        if kn:
            pk = "+".join(parts + ([f"<{kn}>"] if len(kn) > 1 else [kn]))
            logger.debug(f"New hotkey input: {pk}")
            self.hotkeyChanged.emit(self.key, pk)
            
            # UI immediate feedback (pynput format -> display text)
            display_text = pk.replace('<', '').replace('>', '').replace('+', ' + ')
            self.setText(display_text)
            self.stop_recording()

    def stop_recording(self):
        logger.debug(f"Hotkey recording stopped: {self.key}")
        self.is_recording = False
        RECORDING_STATUS['is_recording'] = False
        self.releaseKeyboard()
