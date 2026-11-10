"""[실습 3/3] Postgres 서버 — 진입점 (이전: 02_filesystem/main.py · 다음: 99_ref 슬라이드)
역할: 진입점 — Postgres MCP Pro를 붙여 발견 → 질문을 SQL로 조회(LLM) → 서버 모드별 SELECT/DROP 실험을 실행한다
의존: db (이 디렉터리, 새 층), mcp_client·deepseek_agent (01_basic에서 vendored)
"""
import asyncio
import time

import db
import deepseek_agent
import mcp_client

NEXT_STAGE = "99_ref 슬라이드 (보안·스펙·참고자료)"
REPORT_COLUMNS = ["구분", "status", "elapsed_ms", "입력", "output", "sql"]
LLM_QUESTION = "orders 테이블의 전체 주문 금액(amount) 합계는 얼마인지 SQL로 조회해서 알려줘. 먼저 스키마를 확인해."


async def run_demo() -> list[list]:
    rows: list[list] = []
    for index, mode in enumerate(db.MODES):            # restricted → unrestricted 순으로 서버를 다시 띄운다
        print(f"[{index + 1}] 서버 모드: {mode}")
        async with mcp_client.connect(db.server_params_for(mode)) as session:
            if index == 0:                           # 도구 목록·LLM 데모는 첫 모드에서만 (두 모드에서 같다)
                found = await mcp_client.discover(session)
                print(f"    tools {len(found['tools'])}개:", [t.name for t in found["tools"]])
                print("    LLM이 스키마를 읽고 SQL을 만든다 (DeepSeek tool calling)")
                rows.append(await _ask_llm(session, found["tools"]))
            rows.extend(await db.run_safety_test(session, mode))
    return rows


async def _ask_llm(session, tools) -> list:
    sqls: list[str] = []   # LLM이 실제로 보낸 SQL을 모아 보고서에 남긴다

    async def runner(name: str, args: dict) -> str:
        _, output, _ = await mcp_client.call_tool(session, name, args)
        print(f"    LLM 요청 → tools/call {name}({args})")
        if name == "execute_sql":   # 스키마 조회 → execute_sql 순으로 부르는 과정이 로그에 보인다
            sqls.append(args.get("sql", ""))
        return output

    start = time.perf_counter()
    try:
        answer = await deepseek_agent.deepseek_agent(
            LLM_QUESTION, tools=mcp_client.to_openai_tools(tools), tool_runner=runner
        )
        print(f"    답변: {answer}")
        status, output = "ok", answer
    except Exception as exc:  # noqa: BLE001 — 키 없음·네트워크 오류를 보고서 행으로 남긴다
        print(f"    LLM 호출 실패: {type(exc).__name__}: {exc}")
        status, output = "error", type(exc).__name__
    ms = int((time.perf_counter() - start) * 1000)
    return ["llm: 질문→SQL", status, ms, "주문 합계", db._one_line(output), db._one_line(sqls[-1] if sqls else "-")]


def main() -> None:
    deepseek_agent.load_dotenv()
    rows = asyncio.run(run_demo())
    mcp_client.print_report("03_postgres", REPORT_COLUMNS, rows, footer=f"다음 단계: {NEXT_STAGE}")


if __name__ == "__main__":
    main()
