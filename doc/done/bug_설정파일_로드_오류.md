# 버그 리포트: 설정 파일 로드 및 경로 혼선 문제

## 현상
- 앱 실행 후 웹 UI에서 커스텀 창 크기 비율 수정 및 저장 시, 새로고침하면 정상 적용되고 기능도 작동함.
- 그러나 사용자가 기대하는 설정 파일(작업 디렉토리 내 `app/src/config/config.json`)과 실제 앱이 사용하는 파일(`~/Library/Application Support/WinResizer/config.json`)이 일치하지 않아 로딩 과정에서 혼선 발생 가능성.
- 앱 시작 시 또는 특정 조건에서 설정이 초기화되거나 엉뚱한 파일을 로드하는 현상으로 추측됨.

## 원인 추측
1. `config_manager.py`에서 `CONFIG_FILE` 경로가 `~/Library/Application Support/WinResizer/config.json`으로 고정되어 있음.
2. 개발 환경(Non-frozen)에서도 사용자 홈 디렉토리의 설정만 참조하므로, 소스 코드 트리에 포함된 `config.json` 수정 내용이 반영되지 않음.
3. 앱 시작 시 `load_config` 과정에서 로컬 설정 파일을 먼저 확인하지 않음.

## 조치 내용
1. `config_manager.py`의 `CONFIG_FILE` 결정 로직을 개선.
   - `frozen`(빌드된 상태)이 아닐 경우, `app/src/config/config.json`이 존재하면 이를 우선적으로 사용하도록 수정.
   - 이를 통해 개발 중 에디터에서 편집하는 `config.json`과 앱이 사용하는 설정 파일을 일치시킴.
2. `DEFAULT_CONFIG_FILE` 경로 설정 로직을 `_BASE` 변수를 사용하여 통합 관리하도록 정리.
3. 웹 서버(`web_server.py`) 및 단축키 리스너(`hotkey_listener.py`)에서 `config_manager`를 통해 항상 최신 설정을 참조함을 재검증함.

## 결과
- 이제 개발 환경에서 `app/src/config/config.json`을 직접 수정하거나 UI에서 저장할 때 모두 동일한 파일에 반영되며, 앱 재시작 시에도 해당 설정을 정상적으로 로드함.
