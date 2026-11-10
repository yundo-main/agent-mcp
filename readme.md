# MCP — 에이전트에 손과 발 달아주기

Model Context Protocol(MCP)로 에이전트가 파일·DB 같은 외부 시스템에 표준 방식으로 연결되는 과정을 직접 만들고, 붙이고, 막아 보는 실습 자료.

# 디렉터리 구조

```text
mcp/
├── 00_intro/                       도입 (슬라이드만)
│   └── slides/
│       ├── s01-nm-problem.svg
│       ├── s02-usb-c-analogy.svg
│       ├── s03-host-client-server.svg
│       └── s04-course-flow.svg
│
├── 01_basic/                       기반 — 직접 만든 최소 MCP 서버 (복사(vendor) 시작점)
│   ├── main.py                     진입점 — 서버 기동 → 목록 발견 → 호출 데모
│   ├── server.py                   부품 — Resources·Tools·Prompts 각 1개를 노출하는 데모 서버
│   ├── mcp_client.py               부품 — stdio 연결, list_*/call_tool, print_report
│   ├── deepseek_agent.py           부품 — 교체 가능한 LLM 백엔드 (tool calling)
│   └── slides/
│       ├── s01-three-pillars.svg
│       ├── s02-who-controls.svg
│       ├── s03-handshake-flow.svg
│       ├── s04-server-code.svg
│       ├── s05-client-code.svg
│       ├── s06-file-map.svg
│       ├── s07-run-example.svg
│       ├── s08-review-questions.svg
│       └── s09-review-answers.svg
│
├── 02_filesystem/                  + 오픈 소스 filesystem 서버
│   ├── main.py                     진입점 — fs.py를 실행
│   ├── fs.py                       새 층 — 서버 인자 구성·경계 테스트
│   ├── mcp_client.py               ← 01_basic vendored
│   ├── deepseek_agent.py           ← 01_basic vendored
│   ├── sample_workspace/           허용 디렉터리 기본값 (FS_ROOT를 비우면 사용)
│   │   ├── README.md
│   │   └── notes/
│   │       └── todo.txt
│   └── slides/
│       ├── s01-open-source-server.svg
│       ├── s02-schema-mapping.svg
│       ├── s03-agent-loop.svg
│       ├── s04-allowed-directory.svg
│       ├── s05-boundary-test.svg
│       ├── s06-review-questions.svg
│       └── s07-review-answers.svg
│
├── 03_postgres/                    + Postgres 서버 (완성형)
│   ├── main.py                     진입점 — db.py를 실행
│   ├── db.py                       새 층 — Postgres MCP Pro 기동·SQL 안전 실험
│   ├── mcp_client.py               ← 01_basic vendored
│   ├── deepseek_agent.py           ← 01_basic vendored
│   ├── setup.sql                   샘플 orders 테이블 + 읽기 전용 롤 app_ro
│   ├── overrides.txt               uvx 의존성 대체 (pglast==7.22 — PyPI에 7.2.0이 없음)
│   └── slides/
│       ├── s01-schema-discovery-tools.svg
│       ├── s02-text-to-sql-flow.svg
│       ├── s03-readonly-account.svg
│       ├── s04-drop-denied.svg
│       ├── s05-review-questions.svg
│       └── s06-review-answers.svg
│
├── 99_ref/                         보안·스펙·참고자료 (슬라이드만)
│   └── slides/
│       ├── s01-trust-boundary.svg
│       ├── s02-injection-and-hitl.svg
│       ├── s03-transport-choice.svg
│       ├── s04-spec-sdk-inspector.svg
│       └── s05-cheat-sheet.svg
│
├── logs/                           학생 실행 로그 (.gitkeep만 커밋)
│   └── .gitkeep
│
├── instructor/                     [강사용 — 학생에게 지급하지 않음]
│   ├── plan.md                     과정 설계서
│   ├── prompt.md                   index.html 생성 프롬프트
│   ├── HANDOFF.md                  다른 LLM·작업자에게 넘기는 인수인계 문서
│   ├── tools/                      SVG 슬라이드 생성 스크립트 (svglib.py, gen_*.py)
│   ├── 00_intro/GUIDE.md           단계별 슬라이드 가이드
│   ├── 01_basic/GUIDE.md
│   ├── 02_filesystem/GUIDE.md
│   ├── 03_postgres/GUIDE.md
│   ├── 99_ref/GUIDE.md
│   └── _template/                  과정 생성 템플릿 (README·checklists·prompts·spec·templates)
│
├── index.html                      SVG 슬라이드 인덱스 + 발표 모드
├── readme.md
├── .env.example                    환경변수 템플릿 (.env는 직접 생성, 커밋·배포 제외)
├── .gitignore
└── .distignore                     학생 배포 제외 목록
```

> 현재 완성: 01·02·03 단계의 `.py`, 전 단계(00·01·02·03·99) 슬라이드, `index.html`(5단계 31장 수록).

## 슬라이드 발표

`index.html`을 열고 `▶ 전체 발표`(전 단계) 또는 각 단계의 `▶ 발표`를 누른다. 카드 썸네일을 누르면 그 슬라이드부터 시작한다.
키보드: `←` `→` 이동 · `Space` 다음 · `Home`/`End` 처음·끝 · `F` 전체화면 · `Esc` 닫기.

## 사전 준비

- Python 3.10+, Node.js 24+ (`npx`, 02 단계), `uv` + 로컬 PostgreSQL 14+ (03 단계) — Docker는 필요 없다
- `pip install "mcp[cli]" openai` — `mcp` 2.x 기준 (서버 코드는 `MCPServer`, 1.x의 `FastMCP`가 아니다). DeepSeek API는 OpenAI SDK 호환
- 03 단계: Postgres MCP Pro(`postgres-mcp==0.3.0`)를 `uvx`로 실행한다. 최신 릴리스는 의존성 `pglast==7.2.0`이 PyPI에 없어 그대로는 설치되지 않으므로, `03_postgres/overrides.txt`(`pglast==7.22`)로 대체하고 `--python 3.13 --with "mcp<2"`를 붙인다(서버는 mcp 1.x 기반). `db.py`가 이 인자를 만들어 주므로 학생이 직접 입력할 필요는 없다(2026-11-10 확인).
  - `uv` 설치: `brew install uv` 또는 `pip install uv` (첫 실행 때 Python 3.13과 패키지를 자동으로 받으므로 인터넷 필요)

### 03 단계 DB 준비 (한 번만, macOS 예시)

```bash
brew install postgresql@16
brew services start postgresql@16            # 이미 쓰는 Postgres가 있으면 생략하고 그 DB를 사용
export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"
psql -d postgres -f 03_postgres/setup.sql    # orders 테이블 + 읽기 전용 롤 app_ro 생성
# .env 에 DATABASE_URI=postgresql://app_ro:app_ro_pw@localhost:5432/postgres
# 정리: psql -d postgres -c "DROP TABLE orders; DROP OWNED BY app_ro; DROP ROLE app_ro;" && brew services stop postgresql@16
```

다른 OS는 해당 OS의 PostgreSQL을 설치한 뒤 같은 `psql -f`와 `DATABASE_URI`를 쓰면 된다. 이미 쓰는 Postgres가 있다면 `setup.sql`이 `orders` 테이블과 `app_ro` 롤을 만든다는 점을 확인하고 적용한다.

## 실습 순서

어떤 단계든 **실행할 파일은 항상 `main.py`** — 디렉터리가 목적을, `main.py`가 진입점을 담당한다.

| 순서 | 폴더 | 실행 파일 | 내용 | 실행 |
| --- | --- | --- | --- | --- |
| 0 | (루트) | `.env.example` → `.env` | API 키 설정 | `cp .env.example .env` |
| 1 | `01_basic/` | `main.py` | 직접 만든 서버에서 Resources·Tools·Prompts 발견·호출 | `python3 01_basic/main.py` |
| 2 | `02_filesystem/` | `main.py` | 오픈 소스 filesystem 서버 연결, 경계 밖 접근 거절 확인 | `python3 02_filesystem/main.py` |
| 3 | `03_postgres/` | `main.py` | Postgres 서버 연결, 읽기 전용 계정으로 SQL 조회·DROP 거절 확인 | `python3 03_postgres/main.py` |

각 `main.py` 1행에는 `(이전: X/main.py · 다음: Y/main.py)`가 있어 다음에 어디로 가면 되는지 보인다.
실행 끝에는 실행 로그와 분리된 `[보고서]` 섹션이 출력된다.

## 구조 — main.py + vendored 모듈

1. **모든 디렉터리의 실행 파일은 `main.py`다** — 새로 추가되는 층은 역할이 드러나는 이름의 모듈(`fs.py`, `db.py`)로 분리하고, `main.py`는 그 모듈을 import해 데모만 실행한다.
2. **이전 단계의 모듈은 이름·내용 그대로 복사(vendor)해 가져온다** — 중복처럼 보이지만 의도된 것이다. 사본이 원본과 동일함(`diff`로 검증)이 "이전 층을 건드리지 않았다"는 증거다.
3. **각 디렉터리는 별도의 프로젝트로 간주한다** — `sys.path` 조작·디렉터리 밖 import 금지. `cd {단계} && python3 main.py`만으로 실행된다.
4. **vendored 모듈은 수정하지 않는다** — 단계에서 쓰지 않는 함수(예: 02·03의 `read_resource`)가 있어도 지우지 않는다. 지우면 사본이 원본과 달라져 "이전 층을 건드리지 않았다"는 증거가 사라진다.

| 단계 | main.py가 실행 | 새 층 모듈 | vendored 모듈 |
| --- | --- | --- | --- |
| `01_basic` | 서버 기동 → 발견 → 호출 | — (`mcp_client.py`·`deepseek_agent.py`가 기준) | 없음 |
| `02_filesystem` | filesystem 서버 연결·경계 테스트 | `fs.py` | `mcp_client.py`·`deepseek_agent.py` |
| `03_postgres` | Postgres 서버 연결·SQL 안전 실험 | `db.py` | `mcp_client.py`·`deepseek_agent.py` |
| `99_ref` | — | — | 슬라이드만 |

02와 03은 서로 다른 서버를 붙이는 **형제 단계**라서, `fs.py`는 03으로 가져가지 않는다. 두 단계 모두 01의 클라이언트·백엔드를 그대로 쓴다는 점이 "서버를 바꿔도 클라이언트는 그대로"라는 MCP의 가치를 보여 준다.

각 `.py` 파일 맨 위 docstring에 **RD 표기**(`역할:`+`의존:`)로 관계가 적혀 있다.

### 01_basic 소스코드 트리와 호출 관계

```text
01_basic/
└── main.py                      진입점 — 유일하게 실행하는 파일
     ├─ import ───────▶ mcp_client.py        부품 — 연결·발견·호출·보고서 (02·03 vendoring 기준)
     ├─ import ───────▶ deepseek_agent.py    부품 — LLM tool-calling 루프 (02·03 vendoring 기준)
     └─ 서브프로세스 ──▶ server.py            데모 서버 — @mcp.tool/resource/prompt (이 단계 전용)
                        stdio

호출 관계 (실행 중)
  mcp_client.py     ── JSON-RPC (stdio) ──▶ server.py            */list · call · read · get
  deepseek_agent.py ── HTTPS ──▶ api.deepseek.com               OpenAI 호환 LLM (최대 5턴)
  deepseek_agent.py ── tool_runner ──▶ mcp_client.call_tool     LLM의 tool_call → 다시 서버 호출
  .env              ── load_dotenv ──▶ deepseek_agent.py        DEEPSEEK_API_KEY 주입
```

같은 그림이 `01_basic/slides/s06-file-map.svg`에도 있다.

## 보고서 — 열이 단계마다 늘어난다

`mcp_client.py`의 공통 `print_report(title, columns, rows, footer)`를 모든 단계가 vendoring해서 쓴다.

| 단계 | 열 |
| --- | --- |
| `01_basic` | `[구분, status, elapsed_ms]` (기준) |
| `02_filesystem` | `+ [입력, output]` — 허용 경로 `ok` / 경로 밖 `denied` |
| `03_postgres` | `+ [sql]` — SELECT `ok` / DROP `denied` 또는 `error` |

## 배포 규칙

- `instructor/` 폴더 전체는 학생에게 지급하지 않는다 (`.distignore` 참고).
- 단계 폴더는 수업 단위이자 **독립 프로젝트**다 — 어떤 폴더든 단독으로 떼어 줘도 `main.py`로 완결 실행된다.
- 코드 공유는 `shared/` 디렉터리 대신 vendoring으로 해결한다. `logs/`는 코드가 아니라 학생 실행 로그 보관소다.

## DeepSeek API 사용 (환경변수)

예제는 실제 DeepSeek API를 호출한다. 키와 모델은 환경변수로 지정하며 코드·저장소에 직접 적지 않는다.

방법 1. `.env` 파일 (권장): 프로젝트 루트에서 `cp .env.example .env` 후 키를 적는다. 실행 시 자동으로 읽는다.

방법 2. 셸 환경변수: `export DEEPSEEK_API_KEY="발급받은_키"`. 이미 설정된 환경변수는 `.env`보다 우선한다.

| 환경변수 | 필수 | 기본값 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 필수 | 없음 |
| `DEEPSEEK_MODEL` | 선택 | `deepseek-chat` |
| `DEEPSEEK_BASE_URL` | 선택 | `https://api.deepseek.com` |
| `FS_ROOT` | 선택 | `02_filesystem/sample_workspace` (허용 디렉터리 절대 경로) |
| `DATABASE_URI` | 03 단계 필수 | 없음 (읽기 전용 계정 연결 문자열) |
