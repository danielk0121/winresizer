## 개요
- `WinResizer.spec`의 `datas`에 `app/src/config/` 경로가 포함되어야 번들 빌드 시에도 정상 동작함 (현재 미포함 → 추후 대응 필요)

## 내용
```markdown
❯   추가로 WinResizer.spec의 datas에 app/src/config/가 미포함 상태임을 발견했습니다 — 번들 빌드 시 default-config.json이 포함되지 않으므로 추후 대응이
    필요합니다.

    이게 무슨 말이야. 왜지 ? 빌드할때 config 파일이 포함이 안되는 이유는 뭐야 ? app/src 폴더에 있다는건 소스코드라는 말인데

⏺ 맞습니다. 본질적인 문제가 있습니다.

  default-config.json은 데이터 파일인데 소스코드 폴더(app/src/config/)에 있습니다.

  PyInstaller는 빌드 시 Python 소스코드(.py)는 자동으로 번들에 포함하지만, JSON 같은 데이터 파일은 WinResizer.spec의 datas에 명시해야만 포함됩니다.

  현재 spec 파일을 보면:

  datas=[
      ('app/src/ui/tray_icon.png', 'app/src/ui'),
      ('app/src/templates', 'templates'),
      ('app/src/static', 'static'),
  ],

  app/src/config/가 없습니다. 즉 빌드된 .app 번들 안에 default-config.json이 없으므로 앱 실행 시 기본값 로드에 실패합니다.

  지금 config_manager.py에서 _MEIPASS(PyInstaller 번들 경로) 대응도 안 되어 있습니다.

  두 가지를 동시에 고칩니다.

## 조치 사항 (2026-04-15)
1. **`WinResizer.spec` 수정**:
   - `datas` 항목의 경로를 `app/src/` 구조를 유지하도록 통일했습니다.
   - `config`, `templates`, `static` 폴더가 번들 내부의 `app/src/` 하위에 정확히 위치하도록 설정했습니다.
2. **`config_manager.py` 및 `web_server.py` 수정**:
   - 하드코딩된 경로 계산 로직을 제거하고 `utils.helpers.get_resource_path`를 사용하도록 일원화했습니다.
   - 이로써 개발 환경과 PyInstaller 번들 환경(`_MEIPASS`) 모두에서 리소스를 안전하게 로드할 수 있습니다.

## 결과 확인
- `./build.sh`를 통한 번들 빌드 성공.
- `dist/WinResizer.app/Contents/Resources/app/src/config/default-config.json` 파일 존재 확인 완료.
- `pytest`를 통한 설정 로드 및 웹 서버 초기화 테스트 통과.
- 상세 검증 결과는 `doc/done/verifi_build_res_fix.md`에 기록됨.
```
