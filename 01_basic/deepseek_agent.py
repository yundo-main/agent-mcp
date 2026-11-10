"""[공용] DeepSeek 에이전트 백엔드 — OpenAI 호환 API의 tool calling 루프
역할: 부품 — 교체 가능한 LLM 백엔드. 모든 단계가 이 파일을 그대로 vendoring해 쓴다 (기준 사본: 01_basic)
의존: openai (외부 패키지)
추가: load_dotenv, deepseek_agent
"""
import json
import os
from pathlib import Path

from openai import AsyncOpenAI

DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com"      # DeepSeek는 OpenAI 호환 API를 제공
MAX_TURNS = 5                                       # tool_call 루프 상한 — 무한 호출 방지
SYSTEM_PROMPT = "너는 주어진 도구로 문제를 푸는 도우미다. 필요하면 도구를 호출하고, 결과를 바탕으로 한국어로 간단히 답한다."


def load_dotenv(path: str = ".env") -> None:
    """.env의 KEY=VALUE를 환경변수에 적용한다. 이미 설정된 값이 우선한다"""
    # 단계 폴더에서 실행해도, 프로젝트 루트에서 실행해도 찾도록 위로 올라가며 탐색
    # (setdefault라 셸에 이미 있는 환경변수를 덮어쓰지 않는다)
    for base in [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent, *Path(__file__).resolve().parents]:
        candidate = base / path
        if candidate.is_file():
            for raw in candidate.read_text(encoding="utf-8").splitlines():
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
            return


async def deepseek_agent(prompt: str, tools: list[dict] | None = None, tool_runner=None) -> str:
    """프롬프트를 보내고, 모델이 tool_calls를 내면 tool_runner(name, args)->str로 실행해 결과를 되돌려준다"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY가 설정되지 않았습니다 (.env 또는 환경변수)")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", DEFAULT_BASE_URL),
    )
    model = os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    # tool calling 루프: 모델이 tool_calls를 내면 실행해 결과를 붙이고 다시 묻는다
    for _ in range(MAX_TURNS):
        kwargs = {"model": model, "messages": messages}
        if tools:
            kwargs["tools"] = tools            # MCP에서 온 도구 목록 (to_openai_tools로 변환됨)
        reply = (await client.chat.completions.create(**kwargs)).choices[0].message
        if not reply.tool_calls:               # 더 부를 도구가 없으면 최종 답변
            return reply.content or ""

        messages.append(reply.model_dump(exclude_none=True))   # 어시스턴트 턴을 대화에 추가
        for call in reply.tool_calls:
            args = json.loads(call.function.arguments or "{}")
            output = await tool_runner(call.function.name, args)   # 실제 실행은 호출 측 콜백에 위임
            messages.append({"role": "tool", "tool_call_id": call.id, "content": output})

    return "(도구 호출 횟수 한도를 넘었습니다)"
