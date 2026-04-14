# WinResizer

윈도우 창 크기 조절기 프로젝트입니다. macOS 환경에서 창을 효율적으로 배치하고 관리할 수 있도록 도와줍니다.

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
├── doc/                             # 설계 문서 및 작업 목록 (TODO/Done)
├── spec/                            # 요구사항 명세서
├── ref/                             # 참고 이미지 및 외부 앱 분석 자료
├── build.sh                         # .app 번들 및 DMG 빌드 스크립트
└── WinResizer.spec                  # PyInstaller 빌드 설정
```

### 주요 진입점

- `app/src/main.py`: 앱 진입점 — TrayApp 실행 및 전체 컴포넌트 초기화
- `app/src/tray_app.py`: macOS 메뉴바 트레이 앱 (rumps 기반)
- `app/src/web_server.py`: 설정 및 제어를 위한 Flask 기반 웹 서버

## 실행 중 프로세스 구성

앱 실행 시 **3개의 주요 컴포넌트**가 유기적으로 동작합니다.

| # | 프로세스 / 스레드 | 역할 | 비고 |
|---|---|---|---|
| 1 | **메인 스레드** (rumps TrayApp) | macOS 메뉴바 UI 및 앱 생명주기 관리 | 메인 스레드에서 실행 — macOS AX API 호출 담당 |
| 2 | **HotkeyListenerThread** | 글로벌 키보드 단축키 감지 (pynput) | `threading.Thread` (daemon), 백그라운드 상시 대기 |
| 3 | **Flask 웹 서버 스레드** | 브라우저 기반 설정 UI 및 API 제공 | `threading.Thread` (daemon), 포트는 40000번대 랜덤 할당 |

### Flask 웹 서버 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| `GET` | `/` | 단축키/Gap 설정 페이지 (HTML), 파비콘(favicon.png) 지원 |
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
  └─ 설정 변경 (Highlight 효과)
       └─ POST /api/config
            └─ Flask 웹 서버
                 ├─ config_manager.save_config() → config.json 저장
                 ├─ 캐시 무효화 (ISO 타임스탬프 안내 메시지 출력)
                 └─ HotkeyListenerThread 재시작 → 즉시 새 단축키 반영
```

### 2. 단축키 사용 (창 조절) 시
```
사용자 키 입력
  └─ HotkeyListenerThread (pynput 감지)
       └─ 활성 창 감지 (macOS AX API)
            └─ 현재 모니터 영역 계산 (멀티 모니터 대응)
                 └─ WindowController 실행 (정렬 로직 및 사이클링 적용)
                      └─ 창 위치/크기 업데이트 완료
```

## 스크린샷

![WinResizer 설정 화면](ref/img_4.png)

## 제공 기능
- **분할 배치**: 1/2(상하좌우), 1/3(좌중우), 2/3(좌우), 1/4(모서리) 분할 지원
- **커스텀 비율**: 사용자 정의 비율(예: 60%, 70%) 지원
- **상태 관리**: 최대화, 복구(Restore), 간격(Gap) 조정 가능
- **스마트 사이클링**: 동일 명령 반복 시 창 크기/위치 최적화 순환

## 설치 및 실행 (Quick Guide)

### 1. 가상 환경 및 의존성 설치
본 프로젝트는 `app/venv` 폴더에 가상 환경을 구축하여 사용합니다.
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
- **설정(Preferences...)** 메뉴를 통해 브라우저 설정 페이지를 열 수 있습니다.

### 3. 패키징 및 배포 (독립 실행형 앱)
macOS 환경에서 독립적으로 실행 가능한 앱 번들(.app) 및 DMG를 생성합니다.
```bash
./build.sh
```
빌드 완료 후 `dist/WinResizer.dmg` 파일이 생성됩니다.

## 필수 권한 설정 (macOS)
앱이 정상적으로 창을 제어하기 위해 다음 권한 허용이 필요합니다.
1. **시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용**: 창 제어 권한
2. **시스템 설정 > 개인정보 보호 및 보안 > 입력 모니터링**: 글로벌 단축키 감지 권한
