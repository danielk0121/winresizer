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
```
