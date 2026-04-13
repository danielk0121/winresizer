import sys
import logging
import subprocess
import ApplicationServices
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QScrollArea, QSpinBox, QMessageBox
)
from PyQt5.QtCore import QTimer
from core.hotkey_listener import HotkeyListenerThread
from core.window_controller import execute_window_command
from ui.hotkey_button import HotkeyButton
from core import config_manager
from utils.logger import logger

class WinResizerPreferences(QWidget):
    """
    Main GUI class for WinResizer preferences.
    """
    def __init__(self):
        super().__init__()
        self.hotkey_button_map = {}
        self.current_config = config_manager.get_config()
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save_config_to_disk)
        self.listener_thread = HotkeyListenerThread()
        self.listener_thread.start()
        self.check_permissions()
        self.setup_ui()

    def request_save(self):
        self.save_timer.start(1000)

    def save_config_to_disk(self):
        config_manager.save_config(self.current_config)
        logger.info("설정 파일 저장 완료 (Debounced)")

    def on_gap_changed(self, value):
        if 'settings' not in self.current_config:
            self.current_config['settings'] = {}
        self.current_config['settings']['gap'] = value
        self.request_save()

    def update_hotkey(self, key_name, pynput_str):
        shortcuts = self.current_config.get('shortcuts', {})
        if key_name in shortcuts:
            shortcuts[key_name]['pynput'] = pynput_str
            # ... (UI update)
            self.request_save()


    def check_permissions(self):
        """macOS 접근성 권한 체크"""
        if not ApplicationServices.AXIsProcessTrusted():
            QMessageBox.warning(self, "권한 필요", "창 제어를 위해 '손쉬운 사용' 권한이 필요합니다.\n설정 창에서 권한을 허용해주세요.")
            subprocess.run(["open", "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"])


    def setup_ui(self):
        self.setWindowTitle("WinResizer Settings")
        self.setMinimumSize(570, 1120)
        self.setStyleSheet("background-color: #2b2b2b; color: white;")
        
        main_layout = QVBoxLayout(self)
        
        # 1. Gap setting area
        config = self.current_config
        main_layout.addWidget(QLabel("Gap:"))
        self.gap_spinbox = QSpinBox()
        self.gap_spinbox.setRange(0, 50)
        self.gap_spinbox.blockSignals(True) # 신호 차단
        self.gap_spinbox.setValue(config.get('settings', {}).get('gap', 5))
        self.gap_spinbox.blockSignals(False) # 신호 복구
        self.gap_spinbox.valueChanged.connect(self.on_gap_changed)
        main_layout.addWidget(self.gap_spinbox)

        # 2. Hotkey list area (scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        
        shortcut_config = config.get('shortcuts', {})
        for name, info in shortcut_config.items():
            row = QHBoxLayout()
            
            label = QLabel(name)
            label.setMinimumWidth(100)
            row.addWidget(label)
            
            button = HotkeyButton(info['display'], name)
            button.hotkeyChanged.connect(self.update_hotkey)
            self.hotkey_button_map[name] = button
            row.addWidget(button)
            
            # Individual delete button
            delete_button = QPushButton("✕")
            delete_button.setFixedSize(30, 30)
            delete_button.setToolTip(f"Reset {name} hotkey")
            delete_button.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: #bbb;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e74c3c;
                    color: white;
                }
            """)
            delete_button.clicked.connect(lambda checked, k=name: self.update_hotkey(k, ""))
            row.addWidget(delete_button)
            
            scroll_layout.addLayout(row)
            
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        
        # 3. Bottom control buttons
        clear_all_button = QPushButton("Clear All Hotkeys")
        clear_all_button.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e74c3c;
            }
        """)
        clear_all_button.clicked.connect(self.clear_all_hotkeys)
        main_layout.addWidget(clear_all_button)
        
        quit_button = QPushButton("Quit")
        quit_button.clicked.connect(QApplication.instance().quit)
        main_layout.addWidget(quit_button)

    def on_gap_changed(self, value):
        if 'settings' not in self.current_config:
            self.current_config['settings'] = {}
        self.current_config['settings']['gap'] = value
        self.request_save()
        logger.info(f"Gap setting changed: {value}")

    def update_hotkey(self, key_name, pynput_str):
        logger.info(f"Hotkey updated: {key_name} -> {pynput_str}")
        shortcuts = self.current_config.get('shortcuts', {})
        
        if key_name in shortcuts:
            shortcuts[key_name]['pynput'] = pynput_str
            if pynput_str:
                display_text = pynput_str.replace('<', '').replace('>', '').replace('+', ' + ')
                shortcuts[key_name]['display'] = display_text
            else:
                display_text = "Press hotkey"
                shortcuts[key_name]['display'] = display_text

                
            if key_name in self.hotkey_button_map:
                self.hotkey_button_map[key_name].setText(display_text)
                
            self.request_save()
            logger.info(f"Hotkey saved: {key_name}")

    def clear_all_hotkeys(self):
        reply = QMessageBox.question(self, 'Confirmation', 'Are you sure you want to clear all hotkeys?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            for key in list(self.current_config.get('shortcuts', {}).keys()):
                self.update_hotkey(key, "")
            logger.info("All hotkeys cleared.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WinResizerPreferences()
    window.show()
    sys.exit(app.exec_())
