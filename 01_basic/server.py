"""[실습 1/3] 3대 기둥 — 데모 MCP 서버
역할: 부품 — Resource·Tool·Prompt를 각각 노출하는 최소 서버. 직접 실행하지 않고 main.py가 서브프로세스로 띄운다
의존: mcp (외부 패키지)
추가: add(Tool), about·greeting(Resource), summarize(Prompt)
"""
from mcp.server.mcpserver import MCPServer

SERVER_NAME = "demo"

# 서버 인스턴스 — 아래 데코레이터가 여기에 Tool·Resource·Prompt를 등록한다
mcp = MCPServer(SERVER_NAME)


@mcp.tool()  # Tool: 함수 시그니처와 docstring이 입력 스키마·설명이 된다
def add(a: int, b: int) -> int:
    """두 수를 더한다"""
    return a + b


@mcp.resource("demo://about")  # Resource (고정 주소): list_resources에 나온다
def about() -> str:
    """서버 소개 (고정 주소의 읽을거리)"""
    return "MCP 실습용 데모 서버입니다."


@mcp.resource("greeting://{name}")  # Resource 템플릿: list_resource_templates에 나온다
def greeting(name: str) -> str:
    """이름을 넣으면 인사말을 돌려준다 (주소 템플릿)"""
    return f"안녕하세요, {name}님"


@mcp.prompt()  # Prompt: 사용자가 골라 쓰는 지시문 템플릿
def summarize(text: str) -> str:
    """글을 3줄로 요약하게 하는 프롬프트 템플릿"""
    return f"다음 글을 3줄로 요약하라:\n{text}"


if __name__ == "__main__":
    # stdio 전송: 클라이언트가 이 파일을 서브프로세스로 띄우고 stdin/stdout이 JSON-RPC 채널이 된다
    mcp.run(transport="stdio")
