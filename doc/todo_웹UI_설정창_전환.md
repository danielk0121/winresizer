# TODO: 웹 UI 설정창 전환 (PyQt5 제거)

## 개요
PyQt5 기반 설정 창을 Flask 웹 서버 + 브라우저 UI로 대체한다.
배포 파일 용량 절감이 주목적이며, PyQt5 제거로 설치 후 용량 372MB → ~130MB 예상.

## 배경
- `todo_배포작업3차.md` 분석 결과, PyQt5가 설치 용량의 36%(112MB) 차지
- 핵심 기능(창 크기 조절, 단축키 감지)은 pyobjc, pynput만으로 동작하며 PyQt5와 무관
- GUI는 단축키 설정 입력을 위한 수단이므로 웹 UI로 대체 가능

## 구현 방향

### 아키텍처
- 앱 실행 시 로컬 Flask 서버를 백그라운드로 구동 (예: `http://localhost:5000`)
- 트레이 아이콘 클릭 시 브라우저로 설정 페이지 오픈 (`webbrowser.open`)
- 설정 변경 시 Flask API를 통해 `config.json` 저장 및 단축키 리스너 재시작

### 변경 대상 파일

| 파일 | 변경 내용 |
|---|---|
| `app/src/core/hotkey_listener.py` | `QThread` → `threading.Thread` 교체 |
| `app/src/gui.py` | Flask 서버 구동 및 트레이 아이콘 로직으로 대체 |
| `app/src/ui/hotkey_button.py` | 제거 |
| `app/src/main.py` | QApplication 제거, Flask 서버 + 트레이 진입점으로 변경 |
| `app/requirements.txt` | PyQt5 제거, Flask 추가 |

### 트레이 아이콘
- PyQt5 없이 트레이 아이콘을 유지하기 위해 `rumps` 라이브러리 사용 (macOS 전용, 경량)

### 웹 UI 기능 요구사항
- 단축키 목록 표시 및 편집 (현재 PyQt5 설정 창과 동일한 기능)
- 단축키 녹화 기능 (키 입력 감지 → 표시) — 브라우저에서 `keydown` 이벤트로 구현
- 저장 버튼 클릭 시 즉시 반영 (리스너 재시작)

## 작업 목록 (TODO)

- [ ] `hotkey_listener.py`: `QThread` → `threading.Thread` 교체
- [ ] `main.py`: Flask 서버 + rumps 트레이 진입점으로 변경
- [ ] Flask 라우트 구현: `GET /` 설정 페이지, `GET /api/config`, `POST /api/config`
- [ ] 웹 UI 구현: HTML/CSS/JS 단축키 설정 폼 (단축키 녹화 포함)
- [ ] `gui.py`, `ui/hotkey_button.py` 제거
- [ ] `requirements.txt` 업데이트 (PyQt5 제거, Flask + rumps 추가)
- [ ] 기존 E2E 테스트 수정 (PyQt5 기반 → 웹 기반)
- [ ] 빌드 후 용량 실측 검증

## 검증 기준
- 단축키 설정 변경 후 앱 재시작 없이 즉시 반영되는지 확인
- 브라우저에서 단축키 녹화 기능 정상 동작 확인
- 빌드 후 DMG 용량 ~60MB, 설치 후 ~130MB 이하 확인
