"""
Claude Agent SDK 服务封装
调用 Anthropic Claude SDK，执行 AI 对话
接口与 qoder.py 的 chat_stream() 完全一致
"""

from typing import AsyncIterator, Any, Dict, List, Optional
import asyncio
import os
import json

# Anthropic SDK 集成
try:
    from anthropic import Anthropic
    from anthropic.types import (
        Message,
        MessageStreamEvent,
        TextBlock,
        ToolUseBlock,
        ToolResultBlock,
        ContentBlock,
        TextDelta,
        ToolUseBlockDelta,
        MessageDeltaUsage,
    )
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from claw_gateway.permission import build_permission_hook


async def chat_stream(
    prompt: str,
    session_context: dict,
) -> AsyncIterator[dict]:
    """
    调用 Anthropic Claude SDK 执行对话
    
    Args:
        prompt: 用户消息
        session_context: 用户上下文（含 RBAC 权限）
    
    Yields:
        dict: AI 响应消息，格式与 qoder.py 一致
    """
    # 输入验证
    if not isinstance(prompt, str):
        yield {"type": "error", "error": "prompt 必须是字符串"}
        return
    
    if not isinstance(session_context, dict):
        yield {"type": "error", "error": "session_context 必须是字典"}
        return

    if not ANTHROPIC_AVAILABLE:
        # 开发阶段：模拟响应
        async for msg in _mock_response(prompt):
            yield msg
        return

    # 获取 API Key
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        yield {
            "type": "error",
            "error": "ANTHROPIC_API_KEY 环境变量未设置"
        }
        return

    client = Anthropic(api_key=api_key)

    # 构建权限 Hook
    permission_hook = build_permission_hook(session_context)

    # 从 session_context 获取消息历史（确保为列表）
    message_history = session_context.get("message_history") or []
    
    # 构建 Claude 消息格式
    messages = _build_messages(message_history, prompt)
    
    # 获取允许的工具列表（确保为列表）
    allowed_tools = session_context.get("allowed_tools") or []
    
    # 构建工具列表
    tools = None
    if allowed_tools:
        # 过滤并构建工具定义
        tools = _build_tools(allowed_tools)

    try:
        # 使用流式 API
        with client.messages.stream(
            model="claude-3-5-sonnet-20241022",  # 可以根据需要调整模型
            max_tokens=4096,
            messages=messages,
            tools=tools,
        ) as stream:
            
            # 处理流式事件
            for event in stream:
                # 转换事件为 qoder 格式
                converted = _convert_event(event)
                if converted:
                    yield converted
            
            # 获取最终消息以获取使用统计
            final_message = stream.get_final_message()
            
            # 输出结果消息
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


def _build_messages(message_history: List[dict], current_prompt: str) -> List[Dict]:
    """
    构建 Claude API 消息格式
    
    Args:
        message_history: 历史消息列表
        current_prompt: 当前用户消息
    
    Returns:
        List[Dict]: Claude API 格式的消息列表
    """
    messages = []
    
    # 添加历史消息
    for msg in message_history:
        if msg.get("role") == "user":
            messages.append({
                "role": "user",
                "content": msg.get("content", "")
            })
        elif msg.get("role") == "assistant":
            # 需要处理助理消息中的工具调用
            content = msg.get("content", [])
            if isinstance(content, list):
                # 处理内容块
                content_blocks = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            content_blocks.append({
                                "type": "text",
                                "text": block.get("content", "")
                            })
                        elif block.get("type") == "tool_call":
                            content_blocks.append({
                                "type": "tool_use",
                                "id": block.get("id", ""),
                                "name": block.get("tool", ""),
                                "input": block.get("input", {})
                            })
                messages.append({
                    "role": "assistant",
                    "content": content_blocks
                })
    
    # 添加当前消息
    messages.append({
        "role": "user",
        "content": current_prompt
    })
    
    return messages


def _build_tools(allowed_tools: List[str]) -> List[Dict]:
    """
    根据允许的工具列表构建 Claude 工具定义
    
    Args:
        allowed_tools: 允许的工具名称列表
    
    Returns:
        List[Dict]: Claude API 格式的工具定义
    """
    # 这里需要根据实际工具定义来构建
    # 这是一个简化的示例，实际使用时需要完整的工具定义
    tools = []
    
    # 基础工具定义（需要根据实际工具完善）
    tool_definitions = {
        "Bash": {
            "name": "Bash",
            "description": "执行 bash 命令",
            "input_schema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的 bash 命令"}
                },
                "required": ["command"]
            }
        },
        "Write": {
            "name": "Write",
            "description": "写入文件",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "content": {"type": "string", "description": "文件内容"}
                },
                "required": ["path", "content"]
            }
        },
        "Edit": {
            "name": "Edit",
            "description": "编辑文件",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"},
                    "old_string": {"type": "string", "description": "要替换的字符串"},
                    "new_string": {"type": "string", "description": "替换后的字符串"}
                },
                "required": ["path", "old_string", "new_string"]
            }
        },
        "WebSearch": {
            "name": "WebSearch",
            "description": "执行网页搜索",
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"}
                },
                "required": ["query"]
            }
        }
    }
    
    for tool_name in allowed_tools:
        if tool_name in tool_definitions:
            tools.append(tool_definitions[tool_name])
    
    return tools


def _convert_event(event: MessageStreamEvent) -> Optional[Dict]:
    """
    将 Claude 流式事件转换为 qoder 格式
    
    Args:
        event: Claude 流式事件
    
    Returns:
        Optional[Dict]: 转换后的消息，如果不需要输出则返回 None
    """
    event_type = event.type
    
    if event_type == "content_block_start":
        # 内容块开始
        block = event.content_block
        if block.type == "text":
            return {
                "type": "text",
                "content": block.text
            }
        elif block.type == "tool_use":
            return {
                "type": "tool_call",
                "id": block.id,
                "tool": block.name,
                "input": block.input
            }
    
    elif event_type == "content_block_delta":
        # 内容块增量
        delta = event.delta
        if delta.type == "text_delta":
            return {
                "type": "text",
                "content": delta.text
            }
        elif delta.type == "input_json_delta":
            # 工具调用输入增量 - 使用 content_block_index 作为 ID
            return {
                "type": "tool_call_delta",
                "index": event.index,  # 使用 index 追踪工具调用块
                "input_delta": delta.partial_json
            }
    
    elif event_type == "message_start":
        # 消息开始
        return None  # 不需要输出
    
    elif event_type == "message_delta":
        # 消息增量（如使用统计）
        delta = event.delta
        if delta.stop_reason:
            return {
                "type": "result",
                "subtype": "stop",
                "stop_reason": delta.stop_reason
            }
        return None
    
    elif event_type == "message_stop":
        # 消息结束
        return None
    
    # 其他事件类型
    return {
        "type": event_type.replace("_", " "),
        "data": str(event)
    }


async def _mock_response(prompt: str) -> AsyncIterator[Dict]:
    """
    SDK 未安装时的模拟响应
    
    Args:
        prompt: 用户消息
    
    Yields:
        Dict: 模拟响应消息
    """
    chunks = [
        {"type": "text", "content": "[开发模式] Claude SDK 未安装，收到消息："},
        {"type": "text", "content": prompt[:100]},
        {"type": "text", "content": "...\n\n（请安装 anthropic SDK: pip install anthropic）"},
        {"type": "text", "content": "\n设置环境变量：export ANTHROPIC_API_KEY=your_api_key"},
    ]
    
    for chunk in chunks:
        yield chunk
        await asyncio.sleep(0.1)
    
    # 模拟工具调用（用于测试）
    yield {
        "type": "tool_call",
        "id": "mock_tool_001",
        "tool": "Bash",
        "input": {"command": "echo 'Hello from mock mode'"}
    }
    
    yield {
        "type": "tool_result",
        "tool_use_id": "mock_tool_001",
        "content": "Hello from mock mode",
        "is_error": False
    }
    
    yield {
        "type": "result",
        "subtype": "complete",
        "usage": {"input_tokens": 0, "output_tokens": 0},
        "total_cost_usd": 0.0,
    }


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    """
    估算 API 调用成本（基于 Claude 3.5 Sonnet 定价）
    
    Args:
        input_tokens: 输入 token 数
        output_tokens: 输出 token 数
    
    Returns:
        float: 估算成本（美元）
    """
    # Claude 3.5 Sonnet 定价（2024年10月）
    # Input: $3.00 / 1M tokens
    # Output: $15.00 / 1M tokens
    INPUT_COST_PER_M = 3.00 / 1_000_000
    OUTPUT_COST_PER_M = 15.00 / 1_000_000
    
    return input_tokens * INPUT_COST_PER_M + output_tokens * OUTPUT_COST_PER_M


# 兼容性包装函数
def _convert_message(msg: Any) -> Dict:
    """
    将 Claude SDK 消息转换为 SSE 格式（兼容 qoder.py 接口）
    
    Args:
        msg: Claude SDK 消息
    
    Returns:
        Dict: 转换后的消息
    """
    # 简化实现，实际使用时需要根据 Claude SDK 类型进行转换
    if hasattr(msg, "to_dict"):
        return msg.to_dict()
    
    # 处理常见类型
    if isinstance(msg, dict):
        return msg
    
    # 兜底处理
    return {
        "type": "unknown",
        "content": str(msg)
    }