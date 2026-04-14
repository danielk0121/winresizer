# 버그 리포트: 트레이 아이콘 미표시 및 앱 프리징 이슈

## 현상
- `/Applications/WinResizer.app` 실행 시 프로세스는 구동되는 듯하나, 메뉴 바에 트레이 아이콘이 나타나지 않음.
- 로그 확인 결과 특정 시점(`tray_app.py:17` 초기화 시작)에서 더 이상 진행되지 않고 멈춰있거나 조용히 종료됨.

## 재현 경로
1. `build.sh`를 통한 앱 번들 생성 및 DMG 패키징
2. `/Applications/WinResizer.app` 설치 후 실행
3. 상단 메뉴 바 확인 및 `ps aux`로 프로세스 생존 여부 확인

## 원인 분석 (상세)
이번 이슈는 다음 세 가지 기술적 결함이 복합적으로 발생한 결과임:

### 1. 다중 경로에서의 라이브러리 로딩 실패 (libintl.8.dylib)
- **증상**: `Python.framework` 내부 바이너리가 실행될 때 `@loader_path/libintl.8.dylib`를 찾지 못해 `dlopen` 에러 발생.
- **상세**: PyInstaller는 기본적으로 모든 바이너리를 `Contents/MacOS`에 모으려 하지만, 일부 프레임워크 바이너리는 자신의 위치(`Contents/Frameworks/...`) 기준 상대 경로를 고집함. 호출자가 위치한 모든 디렉토리에 라이브러리가 복사되지 않아 로딩에 실패함.

### 2. 리소스 경로 해결 메커니즘 불일치
- **증상**: 아이콘 파일(`tray_icon.png`)을 찾지 못해 `rumps` 초기화가 실패하거나 기본 텍스트 모드로 진입 시도 중 프리징.
- **상세**: PyInstaller 번들 모드에서 `sys._MEIPASS`가 때때로 `Contents/Resources`가 아닌 `Contents/Frameworks`를 가리키는 현상 발생. 이로 인해 `app/src/ui/tray_icon.png`를 찾는 로직이 실제 파일 위치와 어긋남.

### 3. LSUIElement(Agent App) 초기화 타이밍 이슈
- **증상**: 메뉴바 전용 앱(`LSUIElement: True`) 설정 시, UI 메인 루프가 완벽히 준비되기 전 백엔드 서비스(웹 서버 등)가 시작되면서 GUI 세션과의 연결이 불안정해짐.
- **상세**: `rumps`의 `super().__init__` 과정에서 아이콘 로딩 실패와 겹쳐 UI 쓰레드가 블락되는 현상 확인.

## 해결 방법

### 1. 빌드 스크립트(`build.sh`) 전면 개편
- `libintl.8.dylib`를 `MacOS`, `Frameworks`, `Python.framework` 하위 버전 폴더 등 **모든 예상 로딩 지점에 수동 복사**.
- `install_name_tool`을 사용하여 모든 `.dylib`, `.so`, `Python` 바이너리의 `rpath`와 `dependency`를 `@loader_path` 기반으로 강제 교정.
- 수정으로 깨진 코드 서명을 `codesign --force --deep --sign -` 명령으로 재서명하여 시스템 차단 방지.

### 2. 리소스 탐색 로직 강화 (`helpers.py`)
- `get_resource_path` 함수에서 `sys._MEIPASS`가 `Contents/Frameworks`를 가리킬 경우, 자동으로 상위 폴더인 `Contents/Resources`를 탐색하도록 보정 로직 추가.

### 3. 트레이 앱 초기화 구조 개선 (`tray_app.py`)
- `rumps.App` 초기화 과정을 `try-except`로 감싸 아이콘 로딩 실패 시에도 텍스트 모드로라도 실행되도록 방어 코드 삽입.
- 초기화 순서가 명확히 로그에 남도록 상세 로깅(Detailed Logging) 추가.

## 최종 요약
- **결과**: 라이브러리 로딩 정상화, 리소스 경로 일치, GUI 초기화 안정화를 통해 `/Applications`에 설치된 앱이 백그라운드에서 정상적으로 트레이 아이콘을 띄우고 상주함을 확인 완료.
