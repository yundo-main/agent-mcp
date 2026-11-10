"""[새 층] Postgres MCP Pro 서버 — 기동 인자 구성·SQL 안전 실험
역할: 새 층 — uvx로 서버를 띄우는 인자를 만들고, SELECT/DROP을 서버 모드별로 실행해 보고서 행으로 만든다
의존: mcp_client (vendored, 호출·상태 상수)
추가: database_uri, server_params_for, run_safety_test
"""
import os
from pathlib import Path

import mcp_client

HERE = Path(__file__).resolve().parent
SERVER_COMMAND = "uvx"                  # PyPI 패키지를 임시 환경에 설치해 실행 (Docker·전역설치 불필요)
SERVER_PACKAGE = "postgres-mcp==0.3.0"  # 릴리스 고정
MODES = ("restricted", "unrestricted")  # 같은 실험을 서버 안전 모드 두 개로 반복한다
STATUS_DENIED = "denied"
SELECT_SQL = "SELECT count(*) FROM orders"   # 읽기 — 두 모드 모두 허용돼야 한다
DROP_SQL = "DROP TABLE orders"               # 쓰기 — 모드·DB 롤 두 겹으로 막혀야 한다


def database_uri() -> str:
    """연결 문자열은 환경변수 DATABASE_URI로만 받는다 (코드·출력에 값을 남기지 않는다)"""
    uri = os.getenv("DATABASE_URI")
    if not uri:
        raise RuntimeError("DATABASE_URI가 설정되지 않았습니다 (.env 참고 — 읽기 전용 계정의 연결 문자열)")
    return uri


def server_params_for(mode: str):
    """서버 모드(restricted/unrestricted)별 실행 명령.
    - --python 3.13: postgres-mcp가 요구하는 Python
    - --with "mcp<2": 서버는 mcp 1.x API로 만들어져 2.x와 충돌한다 (클라이언트인 이 과정의 코드와는 별개 환경)
    - --overrides: 의존성 pglast==7.2.0이 PyPI에 없어 7.22로 대체한다
    """
    args = ["--python", "3.13", "--with", "mcp<2", "--overrides", str(HERE / "overrides.txt"),
            SERVER_PACKAGE, f"--access-mode={mode}"]
    return mcp_client.server_params(SERVER_COMMAND, args, env={"DATABASE_URI": database_uri()})


def _one_line(text: str, limit: int = 48) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


def _judge(status: str, output: str, is_write: bool) -> str:
    """이 서버는 SQL 실패도 정상 응답 본문('Error: …')으로 돌려주므로 본문으로 판정한다"""
    failed = status == mcp_client.STATUS_ERROR or output.startswith("Error")
    if not failed:
        return mcp_client.STATUS_OK
    return STATUS_DENIED if is_write else mcp_client.STATUS_ERROR


async def run_safety_test(session, mode: str) -> list[list]:
    """SELECT와 DROP을 실행해 [구분, status, elapsed_ms, 입력, output, sql] 행으로 돌려준다"""
    rows = []
    # restricted는 서버가 DROP을 거절하고, unrestricted는 읽기 전용 DB 롤이 거절한다 — 거절 주체가 다르다
    for label, sql, is_write in [("SELECT", SELECT_SQL, False), ("DROP", DROP_SQL, True)]:
        raw_status, output, ms = await mcp_client.call_tool(session, "execute_sql", {"sql": sql})
        status = _judge(raw_status, output, is_write)
        print(f"    [{mode}] {sql} -> {status}")
        rows.append([f"{mode}: {label}", status, ms, "execute_sql", _one_line(output), sql])
    return rows
