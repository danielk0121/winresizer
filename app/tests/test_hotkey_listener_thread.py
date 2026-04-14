import unittest
import threading
from unittest.mock import patch, MagicMock
from core.hotkey_listener import HotkeyListenerThread


class TestHotkeyListenerThread(unittest.TestCase):
    """HotkeyListenerThread가 threading.Thread 기반으로 동작하는지 검증"""

    def test_is_threading_thread(self):
        """QThread가 아닌 threading.Thread를 상속하는지 확인"""
        self.assertTrue(issubclass(HotkeyListenerThread, threading.Thread))

    def test_not_qthread(self):
        """PyQt5.QThread를 상속하지 않는지 확인"""
        bases = [c.__name__ for c in HotkeyListenerThread.__mro__]
        self.assertNotIn('QThread', bases)

    @patch('core.hotkey_listener.is_accessibility_trusted', return_value=False)
    def test_thread_starts_without_pyqt(self, mock_trusted):
        """PyQt5 없이 스레드가 정상 시작/종료되는지 확인"""
        thread = HotkeyListenerThread()
        thread.daemon = True
        thread.start()
        thread.join(timeout=1)
        # 접근성 권한 없으면 바로 종료되어야 함
        self.assertFalse(thread.is_alive())

    @patch('core.hotkey_listener.is_accessibility_trusted', return_value=False)
    def test_stop_method_exists(self, mock_trusted):
        """stop() 메서드가 존재하는지 확인"""
        thread = HotkeyListenerThread()
        self.assertTrue(hasattr(thread, 'stop'))


if __name__ == '__main__':
    unittest.main()
