# BUG: 웹 UI 단축키/저장 버그 3건

## 버그 1: cmd + alt + 방향키 조합 설정 불가

### 증상
- 브라우저에서 `cmd + alt + ←` 등 방향키 포함 조합 입력 시 단축키가 설정되지 않음
- 방향키(`ArrowLeft` 등)는 브라우저 기본 동작(텍스트 커서 이동 등)과 충돌하여 `e.preventDefault()`가 제대로 작동하지 않는 경우 발생

### 원인
- `app.js` keydown 핸들러에서 `e.key`를 `<arrowleft>` 형태로 변환하는데,
  pynput은 방향키를 `<left>`, `<right>`, `<up>`, `<down>` 으로 인식함
- 즉, 브라우저의 `e.key` → pynput key 이름 변환 누락

### 수정 방향
- `app.js` keydown 핸들러에 방향키 변환 맵 추가:
  - `arrowleft` → `left`
  - `arrowright` → `right`
  - `arrowup` → `up`
  - `arrowdown` → `down`

---

## 버그 2: 저장 및 적용 버튼 클릭 시 앱 종료

### 증상
- 설정 페이지에서 저장 버튼 클릭 시 "Python 응용 프로그램이 예기치 않게 종료되었습니다" 팝업 발생
- 앱(트레이 아이콘) 종료됨

### 원인
- `POST /api/config` 처리 시 기존 HotkeyListenerThread를 `stop()` 후 새 스레드를 시작하는데,
  리스너 재시작 과정에서 예외가 발생하면 메인 프로세스까지 크래시
- 구체적으로: `pynput` 핫키 파싱 시 브라우저에서 넘어온 잘못된 키 문자열(예: `<arrowleft>`)을
  pynput이 인식하지 못해 예외 발생 → 스레드 크래시 → rumps 메인 루프 영향

### 수정 방향
- `hotkey_listener.py`: 리스너 스레드 내부에서 개별 단축키 파싱 실패 시 해당 키만 건너뛰고
  스레드 자체는 계속 유지 (예외 catch 후 로그 경고)
- `web_server.py` `post_config()`: 리스너 재시작 부분을 try/except로 감싸 크래시 방지

---

## 버그 3: 커스텀 비율 적용 버튼 제거 요청

### 증상 (기능 변경 요청)
- 커스텀 비율 섹션의 각 행에 있는 "적용" 버튼 제거
- 단축키 설정 + 저장으로만 사용하는 방식으로 단순화

### 수정 방향
- `index.html`: 커스텀 비율 4개 행에서 `apply-btn` 버튼 제거
- `app.js`: `applyCustomDirect()` 함수 제거

---

## 작업 계획 (TODO)

- [x] 버그 문서 작성
- [x] `app.js`: 방향키 key 이름 변환 맵 추가 (`arrowleft` → `left` 등)
- [x] `web_server.py`: `post_config()` 리스너 재시작 try/except 추가
- [x] `index.html` + `app.js` + `style.css`: 커스텀 비율 적용 버튼 제거
- [x] 전체 테스트 통과 확인 (43개)
- [x] 커밋 푸시
