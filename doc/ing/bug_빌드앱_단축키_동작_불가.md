# 버그 리포트: 빌드된 앱 실행 시 단축키 동작 불가

## 현상
- `/Applications/WinResizer.app` 실행 시 트레이 아이콘은 정상적으로 표시되고 프로세스(`ps aux`)도 확인됨.
- 로그(`winresizer.log`)상으로 `Hotkey engine running`까지 출력되어 리스너는 구동 중인 것으로 보임.
- 그러나 실제 단축키를 눌렀을 때 창 크기 조절이나 위치 이동이 전혀 발생하지 않음.

## 재현 경로
1. `build.sh`로 빌드된 `/Applications/WinResizer.app` 실행.
2. 손쉬운 사용(Accessibility) 권한 부여 확인.
3. 메모장(TextEdit)이나 Finder 등 활성 창에서 단축키 입력.
4. 반응 없음 확인.

## 예상 원인 (가설)
1. **키 이벤트 탭(Event Tap) 차단**: 리스너는 돌고 있으나, macOS 보안 정책상 `pynput`이 실제 시스템 키 이벤트를 가로채지 못함.
2. **키 매핑 불일치**: 빌드된 환경(Standalone)에서의 키 코드 인식이 로컬 개발 환경(Python 직접 실행)과 달라 단축키 매칭 실패.
3. **AXUIElement API 실패**: 창 제어 명령은 실행되나, `set_window_bounds` 내부의 Apple API 호출이 권한 부족이나 타겟팅 오류로 실패함.
4. **포커스 유실**: 앱이 'Agent app(`LSUIElement: True`)'으로 실행되면서 활성 창 객체를 제대로 가져오지 못함.

## 작업 계획
1. [ ] **상세 로깅 추가**: 단축키 입력 시 엔진 내부에서 어떤 키가 인식되는지, 그리고 매칭 시도가 발생하는지 `DEBUG` 로그 강화.
2. [ ] **API 호출 결과 분석**: `set_window_bounds` 호출 시 반환되는 `kAXError` 코드 확인 로직 추가.
3. [ ] **터미널 실행 테스트**: 번들 내부 바이너리를 터미널에서 실행했을 때와 `.app`으로 실행했을 때의 동작 차이 비교.
4. [ ] **pynput 의존성 점검**: 빌드 시 `pynput` 관련 데이터나 라이브러리가 완벽히 포함되었는지 재검토.
