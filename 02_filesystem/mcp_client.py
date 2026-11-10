"""[공용] MCP 클라이언트 기반 — stdio 연결·발견·호출·보고서
역할: 부품 — 모든 단계가 이 파일을 그대로 vendoring해 쓴다 (기준 사본: 01_basic)
의존: mcp (외부 패키지)
추가: server_params, connect, discover, call_tool, read_resource, get_prompt, to_openai_tools, print_report
"""
import time
import unicodedata
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.shared.exceptions import MCPError

# 보고서 status 열에 쓰는 두 값 (denied 같은 단계별 값은 각 층이 추가한다)
STATUS_OK = "ok"
STATUS_ERROR = "error"


def server_params(command: str, args: list[str], env: dict | None = None) -> StdioServerParameters:
    """서브프로세스로 띄울 서버의 실행 명령을 만든다"""
    return StdioServerParameters(command=command, args=args, env=env)


@asynccontextmanager
async def connect(params: StdioServerParameters):
    """서버를 띄우고 initialize 핸드셰이크까지 마친 세션을 돌려준다"""
    # stdio_client: params 명령으로 서버를 서브프로세스로 띄우고 stdin/stdout 파이프를 돌려준다
    async with stdio_client(params) as (read, write):
        # ClientSession: 파이프 위에서 JSON-RPC 요청/응답을 주고받는 세션
        async with ClientSession(read, write) as session:
            await session.initialize()   # 프로토콜 버전·capabilities 교환
            yield session


async def _list_or_empty(call, attr: str) -> list:
    """서버가 지원하지 않는 목록(Method not found)은 빈 목록으로 본다"""
    try:
        return getattr(await call(), attr)
    except MCPError:   # 예: filesystem 서버는 resources·prompts가 없어 Method not found를 반환
        return []


async def discover(session: ClientSession) -> dict:
    """tools·resources·resource templates·prompts 목록을 발견한다 (*/list). 지원하지 않는 기둥은 빈 목록"""
    return {           # 4종을 한 번에 — 02·03에서는 resources/prompts가 비어 온다
        "tools": await _list_or_empty(session.list_tools, "tools"),
        "resources": await _list_or_empty(session.list_resources, "resources"),
        "templates": await _list_or_empty(session.list_resource_templates, "resource_templates"),
        "prompts": await _list_or_empty(session.list_prompts, "prompts"),
    }


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


async def call_tool(session: ClientSession, name: str, arguments: dict) -> tuple[str, str, int]:
    """도구를 호출하고 (status, output, elapsed_ms)를 돌려준다. 예외는 error로 담는다"""
    start = time.perf_counter()
    try:
        result = await session.call_tool(name, arguments)
        # content는 블록 목록 — text 타입만 이어 붙인다 (이미지 등 다른 타입도 올 수 있다)
        text = "".join(c.text for c in result.content if getattr(c, "type", "") == "text")
        status = STATUS_ERROR if result.is_error else STATUS_OK
        return status, text, _elapsed_ms(start)
    except Exception as exc:  # noqa: BLE001 — 데모: 호출 실패를 보고서 행으로 남긴다
        return STATUS_ERROR, f"{type(exc).__name__}: {exc}", _elapsed_ms(start)


async def read_resource(session: ClientSession, uri: str) -> tuple[str, str, int]:
    """리소스를 읽고 (status, output, elapsed_ms)를 돌려준다"""
    start = time.perf_counter()
    try:
        result = await session.read_resource(uri)
        text = "".join(getattr(c, "text", "") for c in result.contents)
        return STATUS_OK, text, _elapsed_ms(start)
    except Exception as exc:  # noqa: BLE001
        return STATUS_ERROR, f"{type(exc).__name__}: {exc}", _elapsed_ms(start)


async def get_prompt(session: ClientSession, name: str, arguments: dict) -> tuple[str, str, int]:
    """프롬프트 템플릿을 가져오고 (status, output, elapsed_ms)를 돌려준다"""
    start = time.perf_counter()
    try:
        result = await session.get_prompt(name, arguments)
        text = "".join(getattr(m.content, "text", "") for m in result.messages)
        return STATUS_OK, text, _elapsed_ms(start)
    except Exception as exc:  # noqa: BLE001
        return STATUS_ERROR, f"{type(exc).__name__}: {exc}", _elapsed_ms(start)


def to_openai_tools(tools) -> list[dict]:
    """MCP Tool 목록을 OpenAI 호환 tools 스키마로 바꾼다 (inputSchema → function.parameters)"""
    # 이 변환 덕분에 MCP 서버의 도구를 OpenAI 호환 LLM에 그대로 건넬 수 있다
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description or "",
                "parameters": t.input_schema,
            },
        }
        for t in tools
    ]


def _width(text: str) -> int:
    """터미널 표시 폭 — 한글 등 전각 문자는 2칸으로 센다"""
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in text)


def print_report(title: str, columns: list[str], rows: list[list], footer: str = "") -> None:
    """실행 로그와 분리된 요약 표를 출력한다 (모든 단계 공통, 열만 늘려 간다)"""
    cells = [[str(c) for c in row] for row in rows]
    # 한글이 섞여도 열이 어긋나지 않게 _width(전각 2칸)로 너비를 잰다 — ljust는 쓰지 않는다
    widths = [max(_width(col), *(_width(r[i]) for r in cells)) for i, col in enumerate(columns)]

    def line(values: list[str]) -> str:
        return " | ".join(v + " " * (w - _width(v)) for v, w in zip(values, widths))

    print(f"\n[보고서] {title}")
    print(line(columns))
    print("-+-".join("-" * w for w in widths))
    for r in cells:
        print(line(r))
    if footer:
        print(footer)
