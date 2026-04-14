# 배포 작업 3차 - 설치 파일 용량 절감

## 개요
현재 배포 파일의 용량이 지나치게 크므로 용량 절감 방안을 분석하고 적용한다.

## 현황

- DMG 파일 용량: 160MB
- DMG 설치 후 앱 용량: 약 400MB
- 파이썬 프로그램 자체 용량: 약 3MB
- PyQt5 등 GUI 프레임워크가 용량의 대부분을 차지하는 것으로 판단

## 용량 분석

### 설치 후 실측 (372MB 기준)

| 구성 요소 | 용량 | 비고 |
|---|---|---|
| PyQt5 (Qt5 라이브러리 포함) | 112MB | GUI 설정 창 전용 |
| Qt 관련 (QtGui, QtWidgets, QtCore 등) | ~22MB | PyQt5 의존 |
| Python 런타임 | ~19MB | PyInstaller 번들 구조상 필수 |
| 나머지 (pyobjc, pynput 등) | ~219MB | 핵심 기능 의존 |

- DMG(150MB)와 설치 후(372MB) 차이는 DMG가 압축 포맷이기 때문. 동일한 파일.
- **PyQt5가 설치 용량의 약 36% 차지**

### PyQt5 역할 분석

- **핵심 기능(창 크기 조절, 단축키 감지)과 완전히 무관** — pyobjc, pynput만으로 동작
- `core/hotkey_listener.py`에서 `QThread`만 사용 (threading.Thread로 교체 가능)
- GUI 설정 창(`gui.py`, `ui/hotkey_button.py`)에서만 실질적으로 사용

### 방안별 검토 결과

| 방안 | 예상 절감 | 판단 |
|---|---|---|
| PyQt5 제거 + GUI 대체 | DMG 150MB→~60MB, 설치 후 372MB→~130MB | **채택** |
| Python 런타임 번들 제거 (LaunchAgent 방식) | 번들 자체 소멸 | 사용자 Python 설치 필요, 배포 편의성 저하 |
| Swift/Objective-C 재작성 | 5MB 이하 가능 | 재작성 비용 과다 |

- 목표 50MB 미만은 Python 런타임 번들링 구조상 현실적으로 불가
- **현실적 목표: DMG ~60MB, 설치 후 ~130MB**

## 작업 결과 (완료)

| 항목 | 이전 | 이후 | 절감 |
|---|---|---|---|
| `.app` 번들 | 80MB | **30MB** | -50MB (-63%) |
| DMG | 150MB | **41MB** | -109MB (-73%) |

- **목표 50MB 미만 달성 (DMG 41MB)**
- 예측(~60MB)보다 더 좋은 결과

## 작업 계획 (TODO)

- [x] `core/hotkey_listener.py`: `QThread` → `threading.Thread` 교체
- [x] GUI 대체 방식 결정 및 구현 (Flask 웹 UI + rumps 트레이)
- [x] `gui.py`, `ui/hotkey_button.py` PyQt5 코드 제거
- [x] `requirements.txt`에서 PyQt5 제거
- [x] 빌드 후 용량 실측 검증
