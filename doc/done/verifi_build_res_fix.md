# 빌드 번들 리소스 누락 버그 수정 검증 결과 (2026-04-15)

## 1. 개요
- **이슈:** `WinResizer.spec`의 `datas` 설정 미흡으로 빌드된 `.app` 번들 내부에서 기본 설정 파일(`default-config.json`) 및 웹 템플릿 파일이 누락되어 실행 시 오류 발생.
- **조치:** `WinResizer.spec`의 `datas` 경로를 일관성 있게 `app/src/` 구조를 유지하도록 수정하고, 소스 코드 내에서 `get_resource_path`를 사용하여 리소스를 참조하도록 개선.

## 2. 검증 방법
1. `./build.sh`를 실행하여 `.app` 번들을 생성.
2. 생성된 `dist/WinResizer.app` 내부의 `Contents/Resources/` 경로를 탐색하여 파일 존재 여부 확인.
3. 기존 테스트(`test_main.py`, `test_web_server.py`)를 통해 개발 환경에서의 경로 문제 여부 재확인.

## 3. 검증 결과 상세

### A. 번들 내부 파일 구조 확인 (성공)
터미널의 `find` 명령어를 통해 다음 파일들이 정확한 위치에 있음을 확인했습니다.
```bash
dist/WinResizer.app/Contents/Resources/app/src/config/default-config.json (존재 확인)
dist/WinResizer.app/Contents/Resources/app/src/templates/index.html (존재 확인)
dist/WinResizer.app/Contents/Resources/app/src/static/app.js (존재 확인)
dist/WinResizer.app/Contents/Resources/app/src/ui/tray_icon.png (존재 확인)
```

### B. 테스트 코드 실행 결과 (성공)
`pytest`를 이용한 설정 로드 및 웹 서버 초기화 테스트 6건 모두 통과.
- `app/tests/test_main.py`: 2 Passed
- `app/tests/test_web_server.py`: 4 Passed

## 4. 결론
- 본 수정으로 인해 **독립 실행형 앱(.app)**으로 빌드되어 배포될 때도 설정값과 UI 리소스를 완벽하게 로드할 수 있게 되었습니다.
- `get_resource_path` 유틸리티를 통한 경로 관리 일원화로 향후 리소스 추가 시에도 경로 문제가 발생할 가능성을 최소화했습니다.
