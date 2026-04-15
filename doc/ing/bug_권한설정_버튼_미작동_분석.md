# 버그 분석 리포트: 권한 설정 버튼 미작동 이슈

## 1. 개요
WinResizer 설치 후 웹 UI 가이드 팝업에서 "시스템 설정 열기" 버튼을 클릭해도 macOS 시스템 설정 창이 열리지 않는 현상 분석 및 해결.

## 2. 원인 분석
### 2.1 프론트엔드 (JS) 버그
- **문제 지점**: `app/src/static/app.js`의 `applyLang()` 함수.
- **상세**: 언어 전환 시 `guideStep1`, `guideStep2` 요소의 내용을 `innerHTML`로 교체하는데, `LANG` 객체의 번역 문구에 버튼 HTML 태그(`<button>`)가 누락되어 있었음.
- **결과**: 페이지 로드 직후 언어 설정이 적용되면서, 원래 HTML에 존재하던 "설정 열기" 버튼이 사라지고 단순 텍스트로 덮어씌워짐. 사용자는 실제 기능을 수행하는 버튼을 볼 수 없게 됨.

### 2.2 UX 및 명명 규칙 혼선
- **문제 지점**: 가이드 팝업 하단의 `guideBtn` (기존 이름: "시스템 설정 열기").
- **상세**: 이 버튼은 원래 권한 설정 후 페이지를 새로고침(`location.reload()`)하는 용도였으나, 이름이 "시스템 설정 열기"로 되어 있어 사용자가 이 버튼이 메인 기능인 것으로 오해함.
- **결과**: 사용자가 사라진 "설정 열기" 버튼 대신 하단의 새로고침 버튼을 클릭하게 되고, 설정 창이 열리지 않는 것으로 인지함.

## 3. 해결 방안
### 3.1 JS 및 HTML 수정
- **번역 문구 보강**: `LANG` 객체의 `guideStep1` 번역 문구에 `<button class="step-btn" onclick="openAccessibilitySettings()">` 태그를 직접 포함시켜 언어 전환 후에도 버튼이 유지되도록 수정.
- **버튼 기능 및 이름 변경**: 하단 버튼(`guideBtn`)의 클릭 핸들러를 `openAccessibilitySettings()`로 변경하고, 이름을 "시스템 설정 열기 (작동 안할 시 클릭)"으로 변경하여 접근성을 높임.

### 3.2 백엔드 보강 (기존 작업 포함)
- `window_controller.py`에서 최신 macOS(Ventura/Sonoma) 호환 URL 스킴 및 AppleScript 폴백 로직을 추가하여 버튼 클릭 시의 동작 신뢰성을 확보함.

## 4. 검증 결과
- **환경**: macOS Monterey (12.6.7) + Applications 폴더 설치 상태.
- **테스트**: 크롬 브라우저를 통한 직접 클릭 테스트.
- **확인**: 버튼 클릭 시 서버 로그에 `Opening accessibility settings...` 및 `Successfully called open for: ...` 로그가 정상 기록됨을 확인.
