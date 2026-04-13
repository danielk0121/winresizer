import sys
import time
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import pytest

from gui import WinResizerPreferences

@pytest.fixture(autouse=True)
def mock_app_components(mocker):
    mocker.patch("gui.WinResizerPreferences.check_permissions")
    mocker.patch("gui.HotkeyListenerThread.start")

def test_initial_hidden_state(qtbot):
    """초기 실행 시 숨김 상태 및 트레이 아이콘 표시 검증"""
    QApplication.setQuitOnLastWindowClosed(False)
    window = WinResizerPreferences()
    qtbot.addWidget(window)

    assert window.isHidden() == True
    assert window.tray_icon.isVisible() == True

def test_close_event_hides_window(qtbot):
    """창 닫기 이벤트 시 앱 종료 대신 숨김 처리 검증"""
    QApplication.setQuitOnLastWindowClosed(False)
    window = WinResizerPreferences()
    qtbot.addWidget(window)
    
    window.show()
    assert window.isVisible() == True
    
    # 닫기 버튼 누름 효과 시뮬레이션
    window.close()
    
    assert window.isHidden() == True

def test_tray_menu_actions(qtbot, mocker):
    """트레이 메뉴의 설정 표시 및 종료 기능 동작 검증"""
    QApplication.setQuitOnLastWindowClosed(False)
    window = WinResizerPreferences()
    qtbot.addWidget(window)
    
    # 1. 설정 메뉴 클릭
    window.show_preferences()
    assert window.isVisible() == True
    
    # 2. 종료 동작 모킹
    mock_quit = mocker.patch.object(QApplication.instance(), "quit")
    
    # 종료 메뉴 액션 확인 및 트리거
    for action in window.tray_icon.contextMenu().actions():
        if "Quit" in action.text() or "종료" in action.text():
            window.quit_app() # action.trigger() 대신 직접 호출하여 모킹 검증
            break
            
    mock_quit.assert_called_once()
