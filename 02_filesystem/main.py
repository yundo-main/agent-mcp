"""[실습 2/3] 오픈 소스 filesystem 서버 — 진입점 (이전: 01_basic/main.py · 다음: 03_postgres/main.py)
역할: 진입점 — 직접 만들지 않은 서버를 같은 클라이언트로 붙여 발견 → 경계 테스트 → LLM 호출을 실행한다
의존: fs (이 디렉터리, 새 층), mcp_client·deepseek_agent (01_basic에서 vendored)
"""
import asyncio
import time

import deepseek_agent
import fs
import mcp_client

NEXT_STAGE = "03_postgres/main.py"
REPORT_COLUMNS = ["구분", "status", "elapsed_ms", "입력", "output"]


async def run_demo() -> list[list]:
    root = fs.resolve_root()
    # 01과 다른 점은 "띄울 명령"뿐 — connect·discover·call_tool은 같은 vendored 코드다
    params = mcp_client.server_params(fs.SERVER_COMMAND, fs.server_args(root))

    async with mcp_client.connect(params) as session:
        print(f"[1] initialize 완료 — 허용 디렉터리: {root}")

        found = await mcp_client.discover(session)
        print("[2] 발견(*/list)")
        print(f"    tools {len(found['tools'])}개:", [t.name for t in found["tools"]])
        print("    resources/prompts:", len(found["resources"]), "/", len(found["prompts"]), "(이 서버는 도구만 제공)")

        # 이 서버는 허용 디렉터리를 도구(list_allowed_directories)로 스스로 알려 준다
        status, output, ms = await mcp_client.call_tool(session, "list_allowed_directories", {})
        print(f"    list_allowed_directories -> {output}")

        print("[3] 경계 테스트")
        rows = await fs.run_boundary_test(session, root)

        print("[4] LLM이 도구를 고른다 (DeepSeek tool calling)")
        rows.append(await _ask_llm(session, found["tools"], root))

    return rows


async def _ask_llm(session, tools, root: str) -> list:
    question = f"{root}/README.md 파일을 읽고 무슨 내용인지 한 줄로 요약해줘."

    async def runner(name: str, args: dict) -> str:
        _, output, _ = await mcp_client.call_tool(session, name, args)
        print(f"    LLM 요청 → tools/call {name}({args})")
        return output

    start = time.perf_counter()
    try:
        answer = await deepseek_agent.deepseek_agent(
            question, tools=mcp_client.to_openai_tools(tools), tool_runner=runner
        )
        print(f"    답변: {answer}")
        status, output = "ok", answer
    except Exception as exc:  # noqa: BLE001 — 키 없음·네트워크 오류를 보고서 행으로 남긴다
        print(f"    LLM 호출 실패: {type(exc).__name__}: {exc}")
        status, output = "error", f"{type(exc).__name__}"
    return ["llm: README 요약", status, int((time.perf_counter() - start) * 1000), "README.md", fs._one_line(output)]


def main() -> None:
    deepseek_agent.load_dotenv()
    rows = asyncio.run(run_demo())
    mcp_client.print_report("02_filesystem", REPORT_COLUMNS, rows, footer=f"다음 단계: {NEXT_STAGE}")


if __name__ == "__main__":
    main()
