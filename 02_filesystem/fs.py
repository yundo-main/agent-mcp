"""[새 층] 오픈 소스 filesystem 서버 — 기동 인자 구성·경계 테스트
역할: 새 층 — 서버 실행 인자(허용 디렉터리)를 만들고, 허용 경로/경계 밖 경로 읽기 결과를 보고서 행으로 만든다
의존: mcp_client (vendored, 호출·상태 상수)
추가: resolve_root, server_args, run_boundary_test
"""
import os
from pathlib import Path

import mcp_client

HERE = Path(__file__).resolve().parent
SERVER_COMMAND = "npx"                                    # 이번엔 서버를 직접 만들지 않는다 — npm 패키지를 받아 실행
SERVER_PACKAGE = "@modelcontextprotocol/server-filesystem"  # 공식 레지스트리의 오픈 소스 서버
STATUS_DENIED = "denied"                                  # 01의 ok/error에 이 층이 추가하는 세 번째 status
OUTSIDE_PATH = "/etc/passwd"                              # 허용 디렉터리 밖 — 반드시 거절돼야 하는 경로


def resolve_root() -> str:
    """허용 디렉터리: 환경변수 FS_ROOT, 없으면 이 폴더의 sample_workspace"""
    return str(Path(os.getenv("FS_ROOT") or HERE / "sample_workspace").resolve())


def server_args(root: str) -> list[str]:
    """서버 시작 인자 — 허용 디렉터리는 여기서만 정해진다 (여러 개면 뒤에 더 붙인다)"""
    # 이 서버는 "허용 디렉터리"를 CLI 인자로 받는다 — 경계는 서버 기동 시점에 정해진다
    return ["-y", SERVER_PACKAGE, root]


def _one_line(text: str, limit: int = 60) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 1] + "…"


async def run_boundary_test(session, root: str) -> list[list]:
    """허용 경로와 경계 밖 경로를 읽어 [구분, status, elapsed_ms, 입력, output] 행으로 돌려준다"""
    cases = [("허용 경로", f"{root}/README.md"), ("경로 밖", OUTSIDE_PATH)]
    rows = []
    for label, path in cases:
        status, output, ms = await mcp_client.call_tool(session, "read_text_file", {"path": path})
        # 경계 밖은 서버가 is_error=True + "Access denied ..." 본문으로 거절한다 → denied로 재분류
        if status == mcp_client.STATUS_ERROR and "Access denied" in output:
            status = STATUS_DENIED
        print(f"    read_text_file({path}) -> {status}")
        rows.append([label, status, ms, path.replace(root, "<FS_ROOT>"), _one_line(output)])
    return rows
