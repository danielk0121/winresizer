# winresizer

윈도우 창 크기 조절기 프로젝트입니다.

## 프로젝트 구조
- **app**: 앱 소스코드
- **spec**: 앱 개발에 필요한 요구사항 명세 기록

## 기능
- (기능을 추가해 주세요)

## 설치 및 실행 (Quick Guide)

### 1. 가상 환경 및 의존성 설치
본 프로젝트는 `app/venv` 폴더에 가상 환경을 구축하여 사용합니다.
```bash
# 가상 환경 생성 (이미 생성된 경우 생략 가능)
python3 -m venv app/venv

# 의존성 설치
source app/venv/bin/activate
pip install pynput pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz
```

### 2. 앱 실행
가상 환경의 파이썬 인터프리터를 사용하여 실행합니다.
```bash
PYTHONPATH=. app/venv/bin/python3 app/src/main.py
```

### 3. 사용 가능한 단축키
| 단축키 | 기능 |
|---|---|
| `Option + Command + Left` | 현재 창을 좌측 50% 분할 배치 |
| `Option + Command + Right` | 현재 창을 우측 50% 분할 배치 |
| `Option + Command + C` | 현재 창을 화면 중앙에 고정 (1200x800) |

### 4. 필수 권한 설정 (macOS)
앱이 정상적으로 창을 제어하기 위해 다음 권한 허용이 필요합니다:
1. **시스템 설정 > 개인정보 보호 및 보안 > 손쉬운 사용 (Accessibility)**: 실행 중인 앱(예: 터미널) 권한 허용.
2. **시스템 설정 > 개인정보 보호 및 보안 > 입력 모니터링 (Input Monitoring)**: 백그라운드 키보드 감지를 위해 권한 허용.
