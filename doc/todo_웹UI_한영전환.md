# TODO: 웹 UI 한영 전환 기능

## 목적

설정 페이지의 모든 텍스트를 한국어/영어로 전환할 수 있는 버튼을 추가한다.
선택된 언어는 `localStorage`에 저장되어 다음 방문 시에도 유지된다.

## UI 배치

- 페이지 우상단에 `KOR / ENG` 토글 버튼 고정 배치
- 현재 활성 언어를 시각적으로 구분 (활성 언어 강조)

## 번역 대상 텍스트 목록

| 구분 | 한국어 | 영어 |
|---|---|---|
| 페이지 제목 | WinResizer 설정 | WinResizer Settings |
| 저장 버튼 | 저장 및 적용 | Save & Apply |
| 초기화 버튼 | 전체 단축키 초기화 | Reset All Hotkeys |
| 저장 완료 메시지 | 저장 완료! 단축키가 즉시 반영되었습니다. | Saved! Hotkeys applied immediately. |
| 저장 실패 메시지 | 저장 실패. | Save failed. |
| 커스텀 섹션 제목 | 커스텀 비율 창 조절 | Custom Ratio Resize |
| 커스텀 섹션 설명 | 비율(1~99%)을 입력하고 단축키를 설정하세요. 적용 버튼으로 즉시 실행도 가능합니다. | Enter a ratio (1~99%) and set a hotkey. Use the Apply button to resize immediately. |
| 커스텀 방향: 좌측 | 좌측 | Left |
| 커스텀 방향: 우측 | 우측 | Right |
| 커스텀 방향: 상단 | 상단 | Top |
| 커스텀 방향: 하단 | 하단 | Bottom |
| 커스텀 적용 버튼 | 적용 | Apply |
| 단축키 섹션 제목 | 단축키 | Hotkeys |
| 단축키 기본 표시 | 단축키 입력 | Press hotkey |
| 단축키 녹화 중 | 키 입력 대기... | Waiting for key... |
| 창 간격 섹션 제목 | 창 간격 (Gap) | Window Gap |
| confirm 초기화 | 전체 단축키를 초기화할까요? | Reset all hotkeys? |
| 비율 오류 메시지 | 비율은 1~99 사이 정수를 입력하세요. | Enter an integer between 1 and 99. |
| 적용 완료 메시지 | {방향} {비율}% 적용 완료 | {direction} {ratio}% applied |

## 구현 방식

- `app.js`에 `LANG` 객체(한/영 텍스트 맵) 정의
- `applyLang(lang)` 함수로 `data-i18n` 속성을 가진 HTML 요소 텍스트 일괄 교체
- `localStorage`에 `lang` 키로 선택 언어 저장 (`'ko'` / `'en'`)
- 페이지 로드 시 저장된 언어 자동 적용 (기본값: `'ko'`)
- `index.html` 각 텍스트 요소에 `data-i18n="키"` 속성 추가

## 작업 계획 (TODO)

- [ ] todo 문서 작성
- [ ] `index.html`: 번역 대상 요소에 `data-i18n` 속성 추가, 우상단 언어 전환 버튼 추가
- [ ] `static/style.css`: 언어 전환 버튼 스타일 추가
- [ ] `static/app.js`: `LANG` 번역 맵, `applyLang()`, `toggleLang()` 구현, localStorage 연동
- [ ] 브라우저에서 한/영 전환 동작 육안 확인
- [ ] 기존 테스트 전체 통과 확인
- [ ] 커밋 푸시

## 검증 기준

- KOR/ENG 버튼 클릭 시 모든 UI 텍스트가 즉시 전환되는지 확인
- 페이지 새로고침 후에도 선택한 언어가 유지되는지 확인
- 기존 단축키 저장/커스텀 비율 적용 기능 정상 동작 확인
- 기존 테스트 전체 통과
