# 커스텀 비율 창 조절 기능

## 목적

사용자가 직접 수치(0~100%)를 입력하여 원하는 비율로 창을 배치할 수 있도록 한다.
예: 창을 좌측 75% 너비로 배치 → `left_custom:75` 모드

## 지원 모드

| mode 문자열 | 동작 |
|---|---|
| `left_custom:N` | 화면 좌측에서 너비 N% 차지, 높이 전체 |
| `right_custom:N` | 화면 우측에서 너비 N% 차지, 높이 전체 |
| `top_custom:N` | 화면 상단에서 높이 N% 차지, 너비 전체 |
| `bottom_custom:N` | 화면 하단에서 높이 N% 차지, 너비 전체 |

- N은 정수 1~99 (0, 100은 의미 없으므로 유효하지 않음)
- 기존 gap 설정 적용
- 기존 스마트 사이클과 독립적으로 동작 (사이클 없음)
- `/api/execute` POST로 `{"mode": "left_custom:75"}` 형태로 호출 가능
- 웹 UI에 커스텀 비율 입력 패널 추가

## 유효성 검사

- N이 정수가 아닌 경우 → 무시 (로그 경고)
- N < 1 또는 N > 99 → 무시 (로그 경고)

## 작업 계획 (TODO)

- [x] todo 문서 작성
- [x] `coordinate_calculator.py`: `left_custom:N`, `right_custom:N`, `top_custom:N`, `bottom_custom:N` 계산 로직 추가
- [x] `window_controller.py`: `parse_custom_mode()`, `is_valid_custom_mode()` 추가, 실행 흐름 분기 추가
- [x] `tests/test_coordinate_calculator.py`: 커스텀 비율 계산 단위 테스트 5개
- [x] `tests/test_window_controller_custom.py`: 파싱/유효성 검사 테스트 13개
- [x] `web_server.py`: HTML 템플릿에 커스텀 비율 입력 UI 추가 (방향 선택 + 비율 입력 + 적용 버튼)
- [x] Chrome E2E 테스트 5개 추가 및 전체 18개 통과
- [x] 커밋 푸시

## 구현 설계

### coordinate_calculator.py 확장

```python
# left_custom:75 → 화면 좌측 75%
if mode.startswith("left_custom:"):
    pct = int(mode.split(":")[1]) / 100
    return (gap, gap, screen_width * pct - gap * 2, screen_height - gap * 2)
```

### window_controller.py 파싱 위치

`execute_window_command()` 내 복구 모드 처리 직후, `determine_next_mode()` 호출 전에
custom 모드 여부를 판별하고 유효성 검사 후 직접 `calculate_window_position()` 호출.

### 웹 UI 입력 패널

```
[방향 선택: 좌 / 우 / 상 / 하]  [비율 입력: ___%]  [적용] 버튼
```
적용 버튼 클릭 시 `POST /api/execute {"mode": "left_custom:75"}` 전송.
