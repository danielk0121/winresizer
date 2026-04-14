# 배포 작업 2차 - 버그 수정

## 개요
`todo_배포_및_설치_완료.md` 버그 리포트에서 제기된 "DMG 설치 후 앱 실행 불가" 문제의 원인 분석 및 수정 작업.

## 버그 원인 분석

**근본 원인:** `.app` 번들로 실행 시 CWD(현재 작업 디렉토리)가 프로젝트 루트가 아닌 `/`(루트)로 변경되어, 상대 경로 기반 파일 접근이 모두 실패.

## 수정 내용

### 1. 로그 경로 버그 수정 (`app/src/utils/logger.py`)
- 기존: `LOG_DIR = "log"` (상대 경로) → `.app` 실행 시 `/log` 생성 시도, 권한 오류로 로거 초기화 크래시
- 수정: `~/Library/Application Support/WinResizer/log` (절대 경로)
- 로그 확인 경로: `~/Library/Application Support/WinResizer/log/winresizer_*.log`

### 2. 설정 파일 경로 버그 수정 (`app/src/core/config_manager.py`)
- 기존: `__file__` 기준 상대 계산 → PyInstaller 번들에서 `_MEIPASS` 내부(읽기 전용)를 가리켜 저장 불가
- 수정: `~/Library/Application Support/WinResizer/config.json` (절대 경로)

### 3. Info.plist 접근성 권한 항목 추가 (`WinResizer.spec` BUNDLE 섹션)
- `NSAccessibilityUsageDescription` 추가: 접근성 권한 요청 시 안내 문구 표시
- `NSAppleEventsUsageDescription` 추가
- `LSUIElement = true` 추가: Dock 아이콘 미표시 (메뉴바 앱 표준 동작)

### 4. 빌드 스크립트 변경 (`build.sh`)
- 기존: PyInstaller 인라인 옵션으로 빌드
- 수정: `WinResizer.spec` 파일을 사용하여 빌드 (`--info-plist` 옵션이 해당 PyInstaller 버전 미지원)

## 검증

- 단위/통합 테스트 16개 중 15개 통과
- 나머지 1개(`test_edge`)는 Edge 브라우저 미실행 환경 의존 E2E로 이번 수정과 무관
- `./build.sh` 실행 → `dist/WinResizer.dmg` 정상 생성 확인

## 잔여 작업

- [ ] DMG 설치 후 실제 앱 실행 테스트 (수동)
- [ ] `~/Library/Application Support/WinResizer/log/` 에서 로그 정상 생성 확인 (수동)
- [ ] 접근성 권한 요청이 터미널이 아닌 WinResizer 앱 자체로 표시되는지 확인 (수동)
