# Flask 웹 서버 랜덤 포트 전환

## 목적

현재 Flask 서버는 포트 5000으로 고정되어 있다.
포트 충돌 가능성을 제거하고 다중 인스턴스 실행 시 충돌을 방지하기 위해 40000번대 랜덤 포트를 사용하도록 변경한다.

## 현황

- `tray_app.py`: `WEB_PORT = 5000` 하드코딩
- `web_server.py`: `run_server(port=5000)` 기본값 5000 하드코딩
- 브라우저 열기: `open_browser(port=5000)` 고정 포트 사용

## 작업 계획 (TODO)

- [x] todo 문서 작성
- [x] `web_server.py`: `find_free_port()` 추가, `run_server()` 포트 미지정 시 랜덤 할당, `(app, port)` 튜플 반환
- [x] `tray_app.py`: `WEB_PORT` 상수 제거, `self.web_port`에 할당된 포트 저장
- [x] `open_browser()` 호출 시 실제 할당된 포트 전달
- [x] README.md 포트 관련 설명 업데이트 (고정 5000 → 랜덤)
- [x] 기존 테스트 15개 통과 확인
- [x] 커밋 푸시

## 구현 방식

OS에 포트 할당을 맡기는 방법(포트 0 바인딩)보다,
40000–49999 범위에서 `socket`으로 사용 가능 여부를 확인 후 선택하는 방식 사용.

```python
import socket
import random

def find_free_port(start=40000, end=49999):
    while True:
        port = random.randint(start, end)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
```

Flask 서버 시작 후 할당된 포트를 TrayApp이 보관하고, `open_browser()` 호출 시 해당 포트 사용.
