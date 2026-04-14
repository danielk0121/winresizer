# 버그 리포트: 트레이 아이콘 미표시 이슈

## 현상
- `/Applications/WinResizer.app` 실행 시 프로세스는 구동되는 것으로 보이나, macOS 상단 메뉴 바에 트레이 아이콘이 나타나지 않음.

## 재현 경로
1. `/Applications/WinResizer.app` 실행 (또는 `open /Applications/WinResizer.app`)
2. macOS 메뉴 바 확인

## 예상 원인 (가설)
1. **권한 문제**: `pyobjc`를 통한 UI 접근 권한(손쉬운 사용 등)이 없거나 거부됨.
2. **패키징 오류**: `PyInstaller`로 빌드된 앱 패키지 내부 리소스(아이콘 파일) 경로 문제.
3. **런타임 에러**: 트레이 앱 초기화 과정에서 예외 발생으로 인한 비정상 종료.
4. **Info.plist 설정**: `LSUIElement` (Agent app) 설정 관련 이슈.

## 작업 결과
1. [x] 로그 확인 및 런타임 에러 점검: `libintl.8.dylib` 로딩 실패 확인
2. [x] `Info.plist` 및 패키지 내부 아이콘 파일 존재 확인: 존재함
3. [x] `tray_app.py` 소스 코드 분석 (아이콘 로딩 로직): `template=True` 부재 확인
4. [x] 원인 파악 및 수정
    - `WinResizer.spec`에 `libintl.8.dylib` 포함 및 `binaries` 추가
    - `build.sh`에 `rpath` 보정 로직 추가 (Python 프레임워크 경로 대응)
    - `tray_app.py`에 `template=True` 적용하여 가시성 확보
5. [x] E2E 테스트를 통한 검증: 앱 정상 구동 및 로그 갱신 확인 완료

## 최종 요약
- **원인**: 패키징 시 `libintl.8.dylib` 누락 및 잘못된 `rpath`로 인한 런타임 크래시. 앱이 실행되지 않아 트레이 아이콘이 표시되지 않았음.
- **해결**: 빌드 설정(`spec`, `build.sh`) 보완 및 실물 앱 설치/재서명 완료.
