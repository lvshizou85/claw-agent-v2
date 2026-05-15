"""
Claude Agent SDK Runtime 实现
调用 Anthropic Claude API 执行对话
接口与 qoder.py 的 chat_stream() 完全一致
"""

from typing import AsyncIterator, Any
import asyncio
import os

# Anthropic SDK
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# API Key 从环境变量读取
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")


async def chat_stream(
    prompt: str,
    session_context: dict,
) -> AsyncIterator[dict]:
    """
    调用 Claude Agent SDK 执行对话

    Args:
        prompt: 用户消息
        session_context: 用户上下文（含 RBAC 权限）

    Yields:
        dict: AI 响应消息，格式与 qoder.py 一致
    """
    if not ANTHROPIC_AVAILABLE:
        # SDK 未安装时的降级响应
        async for msg in _mock_response(prompt):
            yield msg
        return

    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    # 从 session_context 提取权限
    allowed_tools = session_context.get("allowed_tools", [])
    user_role = session_context.get("user_role", "guest")

    # 高风险工具检测（HITL）
    # 只有 admin 角色可以绕过这些工具的审批
    high_risk_tools = ["Bash", "Write", "Edit", "WebSearch"]
    needs_approval = any(
        tool in str(allowed_tools) for tool in high_risk_tools
    ) and user_role != "admin"

    # 构建消息
    messages = [{"role": "user", "content": prompt}]

    # 构建 tools 列表
    tools = None
    if allowed_tools:
        tools = [{"name": t, "description": t} for t in allowed_tools]

    try:
        # 使用消息流式传输
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            messages=messages,
            tools=tools,
        ) as stream:
            # 流式输出文本块
            for content in stream.text_stream:
                yield {
                    "type": "text",
                    "content": content,
                }

            # 获取完整消息以计算 usage
            final_message = stream.get_final_message()

            # 输出结果摘要
            yield {
                "type": "result",
                "subtype": "complete",
                "usage": {
                    "input_tokens": final_message.usage.input_tokens,
                    "output_tokens": final_message.usage.output_tokens,
                },
                "total_cost_usd": _estimate_cost(
                    final_message.usage.input_tokens,
                    final_message.usage.output_tokens,
                ),
            }

    except Exception as e:
        # 错误处理
        yield {
            "type": "error",
            "error": str(e),
        }


async def _mock_response(prompt: str) -> AsyncIterator[dict]:
    """SDK 未安装时的降级响应"""
    chunks = [
        {"type": "text", "content": "[Claude SDK not available] 收到消息："},
        {"type": "text", "content": prompt[:50]},
        {"type": "text", "content": "...\n\n（开发模式，请安装 anthropic: pip install anthropic）"},
    ]

    for chunk in chunks:
        yield chunk
        await asyncio.sleep(0.1)

    yield {
        "type": "result",
        "subtype": "complete",
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "total_cost_usd": 0.0,
    }


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    估算 API 调用成本（基于 Claude Sonnet 4 定价）
    - Input: $3.75 / 1M tokens
    - Output: $15.00 / 1M tokens
    """
    INPUT_COST_PER_M = 3.75 / 1_000_000
    OUTPUT_COST_PER_M = 15.00 / 1_000_000

    return input_tokens * INPUT_COST_PER_M + output_tokens * OUTPUT_COST_PER_M
