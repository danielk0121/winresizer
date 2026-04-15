# WinResizer

WinResizer는 macOS 환경에서 윈도우 창의 크기와 위치를 효율적으로 관리할 수 있도록 설계된 강력한 창 조절 도구입니다. 복잡한 단축키 설정 없이도 직관적인 조작과 스마트한 사이클링 기능을 통해 화면을 최적으로 활용할 수 있습니다.

## 프로젝트 구조

```
winresizer/
├── app/                             # 앱 소스 및 테스트
│   ├── src/                         # 파이썬 소스 코드
│   │   ├── core/                    # 핵심 로직 (창 관리, 설정, 단축키)
│   │   ├── ui/                      # 트레이 아이콘 및 리소스
│   │   ├── static/                  # 웹 UI 정적 파일 (JS, CSS, Favicon)
│   │   └── templates/               # 웹 UI 템플릿 (HTML)
│   └── tests/                       # TDD 기반 테스트 코드
├── doc/                             # 설계 문서 및 작업 목록 (ing/hold/done)
├── build.sh                         # .app 번들 및 DMG 빌드 스크립트
└── WinResizer.spec                  # PyInstaller 빌드 설정
```

### 주요 진입점

- `app/src/main.py`: 앱 진입점 — TrayApp 실행 및 전체 컴포넌트 초기화
- `app/src/tray_app.py`: macOS 메뉴바 트레이 앱 (rumps 기반)
- `app/src/web_server.py`: 설정 및 제어를 위한 Flask 기반 웹 서버
- `app/src/core/window_controller.py`: 창 조절 로직 및 사이클링 구현

## 실행 중 프로세스 구성

앱 실행 시 **3개의 주요 컴포넌트**가 유기적으로 동작합니다.

| # | 프로세스 / 스레드 | 역할 | 비고 |
|---|---|---|---|
| 1 | **메인 스레드** (rumps TrayApp) | macOS 메뉴바 UI 및 앱 생명주기 관리 | macOS AX API 호출 및 앱 종료 담당 |
| 2 | **HotkeyListenerThread** | 글로벌 키보드 단축키 감지 (pynput) | `daemon` 스레드, 백그라운드 상시 대기 |
| 3 | **Flask 웹 서버 스레드** | 브라우저 기반 설정 UI 및 API 제공 | `daemon` 스레드, 40000번대 랜덤 포트 할당 |

### Flask 웹 서버 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/` | 단축키/Gap 설정 페이지 (HTML) |
| `GET` | `/api/status` | 앱 상태 조회 (권한 승인 여부, PID) |
| `GET` | `/api/config` | 현재 설정값 조회 (JSON) |
| `POST` | `/api/config` | 설정 저장 및 단축키 리스너 실시간 재시작 |
| `POST` | `/api/config/reset` | 기본 설정값 반환 (저장 미수행) |
| `POST` | `/api/execute` | 창 조절 명령 즉시 실행 (`{"mode": "left_half"}`) |
| `GET` | `/api/execute` | 창 조절 명령 즉시 실행 (`?mode=left_half`) |

### 로그 파일 경로

- **실시간 로그**: 실행 시 `PID`, `포트`, `시작 시간`이 기록됩니다.
- **로그 롤링**: 날짜/시간별로 로그 파일이 자동 생성되어 비대화를 방지합니다.
  - 경로: `~/Library/Application Support/WinResizer/log/winresizer_YYYYMMDD_HHMMSS_KST.log`
- **설정 파일**: `~/Library/Application Support/WinResizer/config.json`

## 데이터 플로우

### 1. 단축키 설정 변경 시
```
브라우저 (설정 페이지)
  └─ 설정 변경 및 [저장] 클릭
       └─ POST /api/config
            └─ Flask 웹 서버
                 ├─ config_manager.save_config() → config.json 저장
                 ├─ 캐시 무효화 (기존 리스너 설정 초기화)
                 └─ HotkeyListenerThread → 다음 키 입력 시 새 설정 로드 및 반영
```

### 2. 단축키 사용 (창 조절) 시
```
사용자 키 입력
  └─ HotkeyListenerThread (pynput 감지)
       └─ 활성 창 감지 (macOS AX API)
            └─ 현재 모니터 영역 계산 (멀티 모니터 대응)
                 └─ WindowController 실행 (정렬 로직 및 스마트 사이클링 적용)
                      └─ 창 위치/크기 업데이트 완료
```

## 스크린샷

![WinResizer 설정 화면](ref/img_4.png)

## 제공 기능
- **스마트 사이클링**: 동일 명령 반복 시 창 크기/위치 단계적 순환 (예: 1/2 -> 2/3 -> 1/3)
- **멀티 모니터 지원**: 활성 창이 위치한 모니터 자동 감지 및 모니터 간 이동 기능
- **분할 배치**: 1/2(상하좌우), 1/3(좌중우), 2/3(좌우), 1/4(모서리) 분할 지원
- **커스텀 비율**: 사용자 정의 비율(예: 60%, 70%) 지원
- **상태 관리**: 최대화, 복구(Restore), 간격(Gap) 조정 가능
- **자동 레이아웃**: 특정 앱 실행 시 미리 정의된 위치로 자동 배치

## 설치 및 실행 (Quick Guide)

### 1. 가상 환경 및 의존성 설치
```bash
# 가상 환경 생성 및 진입
python3 -m venv app/venv
source app/venv/bin/activate

# 의존성 설치
pip install -r app/requirements.txt
```

### 2. 앱 실행
가상 환경의 파이썬 인터프리터를 사용하여 실행합니다.
```bash
app/venv/bin/python3 app/src/main.py
```
- 실행 후 메뉴바에 WinResizer 아이콘이 표시됩니다.
- **Preferences...** 메뉴를 통해 브라우저 설정 페이지를 열 수 있습니다.

### 3. 패키징 및 배포 (독립 실행형 앱)
```bash
./build.sh
```
빌드 완료 후 `dist/WinResizer.dmg` 파일이 생성됩니다.

## 필수 권한 설정 (macOS 2단계 가이드)

WinResizer가 창 위치를 조정하고 단축키를 감지하려면 macOS 보안 권한이 필요합니다. 웹 UI 상단에서 실시간 권한 상태를 확인할 수 있습니다.

1.  **1단계: 손쉬운 사용 (Accessibility)**:
    *   창 제어를 위해 필수적인 권한입니다.
    *   **⚠️ 중요**: 권한 허용 즉시 앱이 자동 종료될 수 있습니다. 이는 macOS 보안 정책이며 정상이므로, 앱을 다시 실행해 주세요.
2.  **2단계: 입력 모니터링 (Input Monitoring)**:
    *   시스템 전역 단축키 감지를 위해 필요합니다.
3.  **권한 승인됨**: 웹 UI 상단 배지가 초록색으로 변경되면 모든 준비가 완료된 것입니다.

## 자주 묻는 질문 (FAQ)

**Q: 권한을 허용했는데 왜 앱이 갑자기 종료되나요?**
**A:** macOS는 보안을 위해 '손쉬운 사용' 권한이 변경된 앱을 강제로 종료시킵니다. 다시 실행해 주시면 정상적으로 작동합니다.

**Q: 특정 앱에서는 창 조절이 안 돼요.**
**A:** 시스템 설정, 일부 보안 프로그램은 macOS 정책상 외부 제어를 허용하지 않습니다. 그 외 일반적인 앱에서 안 된다면 권한 설정을 확인해 주세요.

---
*WinResizer는 사용자의 생산성 향상을 위해 지속적으로 업데이트되고 있습니다.*
