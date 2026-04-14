# TODO: 웹서버 HTML/CSS/JS 정적 파일 분리

## 목적

현재 `web_server.py`에 HTML/CSS/JS가 `HTML_TEMPLATE` 문자열로 인라인 삽입되어 있어
코드 가독성이 낮고 프론트엔드 편집이 불편하다.
Flask의 `templates/` + `static/` 구조로 분리하여 각 파일을 독립적으로 편집할 수 있도록 한다.

## 현황

- `app/src/web_server.py`: `HTML_TEMPLATE` 문자열 (~240줄) 안에 HTML/CSS/JS 전부 포함
- `render_template_string(HTML_TEMPLATE)` 방식으로 서빙 중
- PyInstaller 번들(`WinResizer.spec`)에 정적 파일 경로 미포함

## 목표 디렉토리 구조

```
app/src/
├── web_server.py
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── app.js
```

## 작업 계획 (TODO)

- [ ] `app/src/templates/index.html` 생성 — HTML 구조만 포함, CSS/JS는 외부 파일 참조
- [ ] `app/src/static/style.css` 생성 — 기존 인라인 CSS 이동
- [ ] `app/src/static/app.js` 생성 — 기존 인라인 JS 이동
- [ ] `web_server.py`: `render_template_string` → `render_template` 교체, Flask 앱 생성 시 `template_folder` / `static_folder` 경로 지정 (PyInstaller `_MEIPASS` 대응)
- [ ] `WinResizer.spec`: `datas`에 `templates/`, `static/` 폴더 추가
- [ ] 앱 직접 실행(`app/venv/bin/python app/src/main.py`) 후 브라우저에서 설정 페이지 정상 동작 확인
- [ ] 기존 단위/통합 테스트 전체 통과 확인
- [ ] 커밋 푸시

## 구현 상세

### web_server.py 변경

```python
import sys, os

def create_app():
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(base, 'templates'),
                static_folder=os.path.join(base, 'static'))
    ...
    @app.route('/')
    def index():
        return render_template('index.html')
```

### index.html

```html
<link rel="stylesheet" href="/static/style.css">
...
<script src="/static/app.js"></script>
```

### WinResizer.spec datas 추가

```python
datas=[
    ('app/src/ui/tray_icon.png', 'app/src/ui'),
    ('app/src/templates', 'templates'),
    ('app/src/static', 'static'),
],
```

## 검증 기준

- 브라우저에서 설정 페이지 정상 렌더링
- 단축키 저장/커스텀 비율 적용 등 기존 기능 모두 정상 동작
- 기존 테스트 전체 통과
