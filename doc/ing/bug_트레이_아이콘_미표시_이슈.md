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
1. [x] 로그 확인 및 런타임 에러 점검: `libintl.8.dylib` 로딩 실패 재확인
2. [x] `Info.plist` 및 패키지 내부 아이콘 파일 존재 확인: 존재하나 경로 매핑 불일치 발견
3. [x] `tray_app.py` 소스 코드 분석 (아이콘 로딩 로직): `template=True` 적용 및 초기화 블로킹 의심
4. [x] 원인 파악 및 수정
    - `WinResizer.spec`에서 아이콘 위치를 리소스 루트('.')로 변경
    - `build.sh` 전면 개편: `libintl.8.dylib`를 수동 복사하고 `install_name_tool`로 `@loader_path` 기반 `rpath` 강제 지정
    - `tray_app.py` 구조 개선: `rumps.Timer`를 사용하여 UI 메인 루프 진입 후 백엔드(웹 서버, 단축키 리스너) 지연 시작으로 안정성 확보
5. [x] 최종 빌드 및 검증: `otool`을 통한 라이브러리 의존성 및 리소스 위치 최종 확인 완료

## 최종 요약
- **원인**: 
    1. PyInstaller가 `libintl.8.dylib`를 번들 내부 깊숙한 곳에 배치하여 실행 파일이 찾지 못하는 현상 지속.
    2. 트레이 앱 초기화 시 백엔드 서비스(웹 서버 등)가 UI 쓰레드를 점유하여 메인 루프 진입이 지연되거나 차단되었을 가능성.
    3. 번들 모드에서의 아이콘 상대 경로 불일치.
- **해결**: 
    - 빌드 스크립트를 통한 라이브러리 직접 배치 및 `rpath` 고정.
    - 트레이 앱 UI 로딩 우선 순위 조정(타이머 사용).
    - 리소스 경로 최적화.

