"""[실습 1/3] 3대 기둥 — 진입점 (이전: 없음 · 다음: 02_filesystem/main.py)
역할: 진입점 — server.py를 서브프로세스로 띄워 발견(list) → 호출(call/read/get) → LLM tool call 순으로 실행한다
의존: server (이 디렉터리, 서버 실행 파일), mcp_client, deepseek_agent
"""
import asyncio
import sys
import time
from pathlib import Path

import deepseek_agent
import mcp_client

HERE = Path(__file__).resolve().parent
SERVER_COMMAND = sys.executable          # 나를 실행한 그 Python으로 서버를 띄운다 (venv 불일치 방지)
SERVER_ARGS = [str(HERE / "server.py")]  # 서버는 별도 프로세스 — 이 파일의 코드를 직접 부르지 않는다
NEXT_STAGE = "02_filesystem/main.py"
LLM_QUESTION = "17 더하기 25는 얼마인지 add 도구로 계산해서 알려줘."
REPORT_COLUMNS = ["구분", "status", "elapsed_ms"]


async def run_demo() -> list[list]:
    rows: list[list] = []                                    # [보고서]에 출력될 [구분, status, elapsed_ms] 행
    params = mcp_client.server_params(SERVER_COMMAND, SERVER_ARGS)

    async with mcp_client.connect(params) as session:        # 서브프로세스 기동 + initialize 핸드셰이크
        print("[1] initialize 완료 — 서버와 연결됨")

        found = await mcp_client.discover(session)           # */list — 서버가 가진 3대 기둥을 묻는다
        print("[2] 발견(*/list)")
        print("    tools    :", [t.name for t in found["tools"]])
        print("    resources:", [str(r.uri) for r in found["resources"]])
        print("    templates:", [t.uri_template for t in found["templates"]])
        print("    prompts  :", [p.name for p in found["prompts"]])

        print("[3] 호출")
        status, output, ms = await mcp_client.call_tool(session, "add", {"a": 2, "b": 3})
        print(f"    tools/call add(2, 3) -> {output}")
        rows.append(["tool: add(2, 3)", status, ms])

        status, output, ms = await mcp_client.read_resource(session, "greeting://MCP")
        print(f"    resources/read greeting://MCP -> {output}")
        rows.append(["resource: greeting://MCP", status, ms])

        status, output, ms = await mcp_client.get_prompt(
            session, "summarize", {"text": "MCP는 에이전트와 외부 시스템을 잇는 표준이다."}
        )
        print(f"    prompts/get summarize -> {output!r}")
        rows.append(["prompt: summarize", status, ms])

        print("[4] LLM이 도구를 고른다 (DeepSeek tool calling)")
        rows.append(await _ask_llm(session, found["tools"]))

    return rows


async def _ask_llm(session, tools) -> list:
    # tool_runner: LLM이 tool_call을 요청할 때 실제 MCP 서버를 호출해 주는 콜백
    async def runner(name: str, args: dict) -> str:
        status, output, _ = await mcp_client.call_tool(session, name, args)
        print(f"    LLM 요청 → tools/call {name}({args}) -> {output}")
        return output

    start = time.perf_counter()
    try:
        answer = await deepseek_agent.deepseek_agent(
            LLM_QUESTION, tools=mcp_client.to_openai_tools(tools), tool_runner=runner
        )  # to_openai_tools: MCP inputSchema → OpenAI function.parameters 변환
        print(f"    답변: {answer}")
        status = "ok"
    except Exception as exc:  # noqa: BLE001 — 키 없음·네트워크 오류를 보고서 행으로 남긴다
        print(f"    LLM 호출 실패: {type(exc).__name__}: {exc}")
        status = "error"
    return ["llm: add 호출 유도", status, int((time.perf_counter() - start) * 1000)]


def main() -> None:
    deepseek_agent.load_dotenv()             # .env에서 DEEPSEEK_API_KEY 등을 읽는다 (없으면 LLM 행만 error)
    rows = asyncio.run(run_demo())
    mcp_client.print_report("01_basic", REPORT_COLUMNS, rows, footer=f"다음 단계: {NEXT_STAGE}")


if __name__ == "__main__":
    main()
