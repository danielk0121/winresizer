import sys
from PyQt5.QtWidgets import QPushButton, QMessageBox
from PyQt5.QtCore import Qt, pyqtSignal
from core.hotkey_listener import RECORDING_STATUS
from core import config_manager
from utils.logger import logger

# 시스템 예약 단축키 (충돌 가능성 높은 목록)
SYSTEM_RESERVED_KEYS = ["<cmd>+<space>", "<cmd>+<shift>+<space>"]

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
            config = config_manager.get_config()
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
        
        # macOS Modifier compensation
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
        kn = {
            Qt.Key_Left: 'left', 
            Qt.Key_Right: 'right', 
            Qt.Key_Up: 'up', 
            Qt.Key_Down: 'down'
        }.get(k, chr(k).lower() if 32 <= k <= 126 else None)
        
        if kn:
            pk = "+".join(parts + ([f"<{kn}>"] if len(kn) > 1 else [kn]))
            
            # 충돌 검사
            if pk in SYSTEM_RESERVED_KEYS:
                logger.warning(f"Hotkey conflict detected: {pk}")
                QMessageBox.warning(self, "단축키 충돌 경고", f"입력하신 단축키 '{pk}'는 macOS 시스템 예약 단축키와 충돌할 수 있습니다. 다른 조합을 사용해주세요.")
                return

            logger.debug(f"New hotkey input: {pk}")
            self.hotkeyChanged.emit(self.key, pk)
            
            # UI immediate feedback
            display_text = pk.replace('<', '').replace('>', '').replace('+', ' + ')
            self.setText(display_text)
            self.stop_recording()

    def stop_recording(self):
        logger.debug(f"Hotkey recording stopped: {self.key}")
        self.is_recording = False
        RECORDING_STATUS['is_recording'] = False
        self.releaseKeyboard()
