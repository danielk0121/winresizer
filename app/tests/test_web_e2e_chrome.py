"""
웹서버 기반 창 조절 E2E 테스트

테스트 흐름:
1. Flask 웹 서버를 백그라운드 스레드로 실행
2. Google Chrome을 열어 테스트 대상 창으로 사용
3. POST /api/execute 로 창 조절 명령 전송
4. macOS Accessibility API로 실제 창 좌표를 읽어 검증

실행 조건:
- 접근성(Accessibility) 권한 필요
- Google Chrome 설치 필요
"""
import time
import threading
import subprocess
import unittest
import requests
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(os.path.dirname(current_dir), 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from AppKit import NSWorkspace
from ApplicationServices import (
    AXUIElementCreateApplication,
    AXUIElementCopyAttributeValue,
    kAXFocusedWindowAttribute,
)
from core.window_manager import get_window_bounds, is_accessibility_trusted
from core.monitor_info import get_all_monitors_info

TEST_PORT = 15001
BASE_URL = f'http://127.0.0.1:{TEST_PORT}'


def get_chrome_window():
    """실행 중인 Chrome 창 객체를 반환"""
    ws = NSWorkspace.sharedWorkspace()
    for app in ws.runningApplications():
        if 'Google Chrome' in (app.localizedName() or ''):
            pid = app.processIdentifier()
            app_obj = AXUIElementCreateApplication(pid)
            res, win = AXUIElementCopyAttributeValue(app_obj, kAXFocusedWindowAttribute, None)
            if res == 0 and win:
                app.activateWithOptions_(1 << 1)  # NSApplicationActivateIgnoringOtherApps
                time.sleep(0.3)
                return win
    return None


def focus_chrome():
    """Chrome을 frontmost로 올린 뒤 잠시 대기"""
    ws = NSWorkspace.sharedWorkspace()
    for app in ws.runningApplications():
        if 'Google Chrome' in (app.localizedName() or ''):
            app.activateWithOptions_(1 << 1)
            time.sleep(0.5)
            return


def execute(mode):
    """
    Chrome을 포커스시킨 뒤 window_controller를 직접 호출.
    macOS AX API는 메인 스레드에서만 동작하므로 Flask 스레드를 우회한다.
    """
    from core.window_controller import execute_window_command
    focus_chrome()
    execute_window_command(mode)
    time.sleep(0.6)  # 창 이동 완료 대기


class TestWebE2EChrome(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # 1. 접근성 권한 확인
        if not is_accessibility_trusted():
            raise unittest.SkipTest("접근성 권한 없음 — 시스템 설정에서 터미널에 권한을 부여하세요.")

        # 2. Flask 서버 시작
        from web_server import create_app
        app = create_app()
        cls.server_thread = threading.Thread(
            target=lambda: app.run(host='127.0.0.1', port=TEST_PORT, debug=False, use_reloader=False),
            daemon=True
        )
        cls.server_thread.start()

        # 서버 준비 대기
        for _ in range(20):
            try:
                requests.get(BASE_URL, timeout=1)
                break
            except Exception:
                time.sleep(0.3)

        # 3. Chrome 실행
        subprocess.run(['open', '-a', 'Google Chrome', 'about:blank'])
        time.sleep(2.5)

        cls.chrome_win = get_chrome_window()
        if not cls.chrome_win:
            raise unittest.SkipTest("Chrome 창을 찾을 수 없습니다.")

        # 4. 모니터 정보 수집
        monitors = get_all_monitors_info()
        bounds = get_window_bounds(cls.chrome_win)
        cx = bounds[0] + bounds[2] // 2
        cy = bounds[1] + bounds[3] // 2
        cls.monitor = next(
            (m for m in monitors if m['x'] <= cx < m['x'] + m['width'] and m['y'] <= cy < m['y'] + m['height']),
            monitors[0]
        )
        cls.initial_bounds = bounds

        # gap 설정값 로드
        from core import config_manager
        config = config_manager.load_config()
        cls.gap = config.get('settings', {}).get('gap', 5)

        print(f"\n[설정] 모니터: {cls.monitor}")
        print(f"[설정] Chrome 초기 좌표: {cls.initial_bounds}")
        print(f"[설정] gap: {cls.gap}")

    def _bounds(self):
        return get_window_bounds(self.chrome_win)

    def _assert_position(self, bounds, expected_x=None, expected_y=None, expected_w=None, expected_h=None, delta=20):
        x, y, w, h = bounds
        if expected_x is not None:
            self.assertAlmostEqual(x, expected_x, delta=delta, msg=f"x 불일치: {x} != {expected_x}")
        if expected_y is not None:
            self.assertAlmostEqual(y, expected_y, delta=delta, msg=f"y 불일치: {y} != {expected_y}")
        if expected_w is not None:
            self.assertAlmostEqual(w, expected_w, delta=delta, msg=f"width 불일치: {w} != {expected_w}")
        if expected_h is not None:
            self.assertAlmostEqual(h, expected_h, delta=delta, msg=f"height 불일치: {h} != {expected_h}")

    # ── API 헬스 체크 ──────────────────────────────────────────

    def test_00_server_health(self):
        """Flask 서버가 정상 응답하는지 확인"""
        res = requests.get(BASE_URL)
        self.assertEqual(res.status_code, 200)
        print("\n[OK] 서버 응답 정상")

    def test_01_execute_api_invalid(self):
        """mode 없이 /api/execute 호출 시 400 반환 (API 계층 검증)"""
        res = requests.post(f'{BASE_URL}/api/execute', json={}, timeout=5)
        self.assertEqual(res.status_code, 400)
        print("\n[OK] 잘못된 요청 400 반환 정상")

    # ── 1/2 분할 ──────────────────────────────────────────────

    def test_10_left_half(self):
        """좌측 절반 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('left_half')
        b = self._bounds()
        print(f"[좌측_절반] {b}")
        self._assert_position(b,
            expected_x=m['x'] + gap,
            expected_w=m['width'] // 2 - gap * 2,
        )

    def test_11_right_half(self):
        """우측 절반 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('right_half')
        b = self._bounds()
        print(f"[우측_절반] {b}")
        self._assert_position(b,
            expected_x=m['x'] + m['width'] // 2 + gap,
        )

    def test_12_top_half(self):
        """상단 절반 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('top_half')
        b = self._bounds()
        print(f"[위쪽_절반] {b}")
        self._assert_position(b,
            expected_y=m['y'] + gap,
            expected_h=m['height'] // 2 - gap * 2,
        )

    def test_13_bottom_half(self):
        """하단 절반 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('bottom_half')
        b = self._bounds()
        print(f"[아래쪽_절반] {b}")
        self._assert_position(b,
            expected_y=m['y'] + m['height'] // 2 + gap,
        )

    # ── 최대화 & 복구 ──────────────────────────────────────────

    def test_20_maximize(self):
        """최대화 검증"""
        m = self.monitor
        gap = self.gap
        execute('maximize')
        b = self._bounds()
        print(f"[최대화] {b}")
        self._assert_position(b,
            expected_x=m['x'] + gap,
            expected_y=m['y'] + gap,
        )

    def test_21_restore(self):
        """복구(Restore) — 최대화 후 원래 크기로 복원되는지 검증"""
        # 최대화 후 복구
        execute('maximize')
        time.sleep(0.5)
        execute('복구')  # 복구는 한국어 그대로
        b = self._bounds()
        print(f"[복구] {b}")
        # 초기 좌표와 비교 (delta 크게: 복구는 대략적으로 맞으면 됨)
        for i, val in enumerate(b):
            self.assertAlmostEqual(val, self.initial_bounds[i], delta=50,
                msg=f"복구 후 좌표[{i}] 불일치: {val} != {self.initial_bounds[i]}")

    # ── 1/4 분할 ──────────────────────────────────────────────

    def test_30_top_left_quarter(self):
        """좌상단 1/4 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('top_left_1/4')
        b = self._bounds()
        print(f"[좌상단_1/4] {b}")
        self._assert_position(b,
            expected_x=m['x'] + gap,
            expected_y=m['y'] + gap,
        )

    def test_31_top_right_quarter(self):
        """우상단 1/4 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('top_right_1/4')
        b = self._bounds()
        print(f"[우상단_1/4] {b}")
        self._assert_position(b,
            expected_x=m['x'] + m['width'] // 2 + gap,
            expected_y=m['y'] + gap,
        )

    def test_32_bottom_left_quarter(self):
        """좌하단 1/4 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('bottom_left_1/4')
        b = self._bounds()
        print(f"[좌하단_1/4] {b}")
        self._assert_position(b,
            expected_x=m['x'] + gap,
            expected_y=m['y'] + m['height'] // 2 + gap,
        )

    def test_33_bottom_right_quarter(self):
        """우하단 1/4 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('bottom_right_1/4')
        b = self._bounds()
        print(f"[우하단_1/4] {b}")
        self._assert_position(b,
            expected_x=m['x'] + m['width'] // 2 + gap,
            expected_y=m['y'] + m['height'] // 2 + gap,
        )

    # ── 커스텀 비율 ───────────────────────────────────────────

    def test_50_left_custom_75(self):
        """좌측 75% 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('left_custom:75')
        b = self._bounds()
        print(f"[좌측_75%] {b}")
        expected_w = m['width'] * 0.75 - gap * 2
        self._assert_position(b,
            expected_x=m['x'] + gap,
            expected_w=expected_w,
        )

    def test_51_right_custom_30(self):
        """우측 30% 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('right_custom:30')
        b = self._bounds()
        print(f"[우측_30%] {b}")
        expected_x = m['x'] + m['width'] * 0.70 + gap
        self._assert_position(b,
            expected_x=expected_x,
        )

    def test_52_top_custom_60(self):
        """상단 60% 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('top_custom:60')
        b = self._bounds()
        print(f"[상단_60%] {b}")
        expected_h = m['height'] * 0.60 - gap * 2
        self._assert_position(b,
            expected_y=m['y'] + gap,
            expected_h=expected_h,
        )

    def test_53_bottom_custom_40(self):
        """하단 40% 배치 검증"""
        m = self.monitor
        gap = self.gap
        execute('bottom_custom:40')
        b = self._bounds()
        print(f"[하단_40%] {b}")
        expected_y = m['y'] + m['height'] * 0.60 + gap
        self._assert_position(b,
            expected_y=expected_y,
        )

    def test_54_invalid_custom_ignored(self):
        """유효하지 않은 커스텀 비율(0, 100)은 창이 이동하지 않아야 함"""
        execute('left_half')
        b_before = self._bounds()
        execute('left_custom:0')
        b_after = self._bounds()
        self.assertAlmostEqual(b_before[0], b_after[0], delta=20, msg="무효 모드에서 창이 이동함")

    # ── 커스텀 비율 단축키 설정 저장 ─────────────────────────────

    def test_55_custom_mode_saved_on_config_post(self):
        """POST /api/config 로 Left Custom mode 저장 시 비율값이 반영되는지 검증"""
        import requests as req
        res = req.get(f'{BASE_URL}/api/config', timeout=5)
        cfg = res.json()
        cfg['shortcuts']['Left Custom']['mode'] = 'left_custom:60'
        post_res = req.post(f'{BASE_URL}/api/config', json=cfg, timeout=5)
        self.assertEqual(post_res.status_code, 200)

        # 저장된 값 확인
        res2 = req.get(f'{BASE_URL}/api/config', timeout=5)
        updated = res2.json()
        self.assertEqual(updated['shortcuts']['Left Custom']['mode'], 'left_custom:60',
                         "Left Custom mode가 저장된 비율(60)을 반영해야 함")
        print("\n[OK] Left Custom mode 저장/조회 정상")

    def test_56_all_custom_directions_independent(self):
        """좌/우/상/하 커스텀 비율이 각각 독립적으로 동작하는지 검증"""
        m = self.monitor
        gap = self.gap

        # 먼저 최대화로 충분한 크기 확보 후 각 방향 검증
        execute('maximize')
        time.sleep(0.3)

        execute('left_custom:50')
        b_left = self._bounds()
        expected_w_left = m['width'] * 0.50 - gap * 2
        self._assert_position(b_left, expected_x=m['x'] + gap, expected_w=expected_w_left)
        print(f"[좌측_50%] {b_left}")

        execute('right_custom:40')
        b_right = self._bounds()
        expected_x_right = m['x'] + m['width'] * 0.60 + gap
        self._assert_position(b_right, expected_x=expected_x_right)
        print(f"[우측_40%] {b_right}")

        execute('top_custom:50')
        b_top = self._bounds()
        expected_h_top = m['height'] * 0.50 - gap * 2
        self._assert_position(b_top, expected_y=m['y'] + gap, expected_h=expected_h_top)
        print(f"[상단_50%] {b_top}")

        execute('bottom_custom:60')
        b_bottom = self._bounds()
        expected_y_bottom = m['y'] + m['height'] * 0.40 + gap
        self._assert_position(b_bottom, expected_y=expected_y_bottom)
        print(f"[하단_60%] {b_bottom}")



if __name__ == '__main__':
    unittest.main(verbosity=2)
