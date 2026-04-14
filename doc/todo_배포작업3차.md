# 배포 작업 3차 - 설치 파일 용량 절감

## 개요
현재 배포 파일의 용량이 지나치게 크므로 용량 절감 방안을 분석하고 적용한다.

## 현황

- DMG 파일 용량: 160MB
- DMG 설치 후 앱 용량: 약 400MB
- 파이썬 프로그램 자체 용량: 약 3MB
- PyQt5 등 GUI 프레임워크가 용량의 대부분을 차지하는 것으로 판단

## 용량 절감 방안 (TODO)

- [ ] PyInstaller `--exclude-module` 옵션으로 불필요한 모듈 제거
- [ ] PyQt5 → PySide6 또는 경량 프레임워크(rumps 등) 전환 검토
- [ ] UPX 압축 효과 측정 (현재 `build.sh`에 UPX 옵션 적용 중)
- [ ] `pip install` 시 불필요한 의존성 정리 (`requirements.txt` 슬림화)
