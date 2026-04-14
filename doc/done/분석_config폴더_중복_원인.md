# config 폴더 중복 생성 원인 분석

## 현상

프로젝트 내에 `config` 폴더가 두 곳에 존재한다.

```
app/config/          ← 불필요, 빈 폴더, git 미추적
app/src/config/      ← 정상, default-config.json 위치
```

## 원인 분석

### 1. 정상 경로: `app/src/config/`

`config_manager.py`의 경로 계산:

```python
_SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# __file__ = app/src/core/config_manager.py
# _SRC_DIR  = app/src
DEFAULT_CONFIG_FILE = os.path.join(_SRC_DIR, "config", "default-config.json")
# → app/src/config/default-config.json  ✅
```

코드가 어느 디렉토리에서 실행되든 `__file__`은 절대경로로 평가되므로 항상 `app/src/config/`를 가리킨다.

### 2. 잘못 생성된 경로: `app/config/`

#### 생성 시각

```
Apr 14 16:10 (수정) / Apr 14 07:19 (생성)
```

- 가장 근접한 커밋: `3a50f0e` (Apr 14 16:16) — `.app 번들 실행 시 로그/설정 경로 버그 수정`
- 이 커밋에서 `app/Info.plist`를 `app/` 디렉토리에 직접 추가하는 작업을 수행함

#### 유력한 원인: IDE(JetBrains) 자동 생성 또는 수동 오조작

- `.idea/` 폴더가 프로젝트에 존재 → JetBrains IDE 사용 중
- `app/Info.plist` 파일을 IDE에서 `app/` 디렉토리 하위에 추가하는 과정에서 **IDE가 리소스 폴더로 `app/config/`를 자동 인식하거나 수동으로 잘못 생성**한 것으로 추정
- git은 빈 폴더를 추적하지 않으므로 커밋 이력에서 생성 원인이 남지 않음

#### 과거 코드 방식과의 관계 (무관)

초기 `config_manager.py`는 `BASE_DIR` 방식을 사용했으나 항상 `app/src/config/`를 정확히 계산했다. 코드가 `app/config/`를 만든 경우는 없다.

```python
# 구버전 (3164722 이전)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, "config", "config.json")
# __file__ = app/src/core/config_manager.py → BASE_DIR = app/src → app/src/config/config.json
```

## 현재 구조 (정상)

| 파일 | 위치 | 설명 |
|---|---|---|
| `default-config.json` | `app/src/config/` | 기본값 (소스 관리) |
| `config.json` | `~/Library/Application Support/WinResizer/` | 사용자 설정 (런타임 생성) |

## 조치

`app/config/` 빈 폴더는 삭제한다. git이 추적하지 않으므로 커밋 불필요.

```bash
rmdir app/config
```

## 재발 방지

- `app/src/config/` 이외의 위치에 config 관련 폴더가 생기면 즉시 삭제
- `WinResizer.spec`의 `datas`에 `app/src/config/` 경로가 포함되어야 번들 빌드 시에도 정상 동작함 (현재 미포함 → 추후 대응 필요)
