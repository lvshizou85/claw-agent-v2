"""
测试 claude_runtime.py 模块

测试要求：
1. 基础功能测试
2. 消息格式测试
3. 流式响应测试
4. 会话上下文测试
"""

import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List, Dict, Any
import json

# 导入被测试模块
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 直接导入模块
import importlib.util
spec = importlib.util.spec_from_file_location(
    'claude_runtime', 
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'services', 'claude_runtime.py')
)
module = importlib.util.module_from_spec(spec)
sys.modules['claude_runtime'] = module
spec.loader.exec_module(module)

from claude_runtime import (
    chat_stream,
    _mock_response,
    _estimate_cost,
    _build_messages,
    _build_tools,
    _convert_event,
    ANTHROPIC_AVAILABLE,
)


class TestBasicFunctionality:
    """基础功能测试"""
    
    @pytest.mark.asyncio
    async def test_chat_stream_function_exists_and_callable(self):
        """测试 chat_stream 函数存在且可调用"""
        # 验证函数存在
        assert hasattr(chat_stream, '__call__')
        assert asyncio.iscoroutinefunction(chat_stream)
        
        # 验证函数签名
        import inspect
        sig = inspect.signature(chat_stream)
        params = list(sig.parameters.keys())
        assert params == ['prompt', 'session_context']
        
    @pytest.mark.asyncio
    async def test_simulated_mode_when_sdk_not_installed(self):
        """测试模拟模式（SDK 未安装时）"""
        # 模拟 ANTHROPIC_AVAILABLE = False 的情况
        with patch('claw_gateway.services.claude_runtime.ANTHROPIC_AVAILABLE', False):
            prompt = "Hello, Claude!"
            session_context = {"user_role": "guest"}
            
            results = []
            async for msg in chat_stream(prompt, session_context):
                results.append(msg)
            
            # 验证有响应返回
            assert len(results) > 0
            
            # 验证消息格式
            for msg in results:
                assert "type" in msg
                assert msg["type"] in ["text", "tool_call", "tool_result", "result", "error"]
    
    @pytest.mark.asyncio
    async def test_api_key_missing_handling(self):
        """测试 API Key 缺失处理"""
        # 模拟 SDK 可用但无 API Key 的情况
        with patch('claw_gateway.services.claude_runtime.ANTHROPIC_AVAILABLE', True):
            with patch.dict(os.environ, {}, clear=True):
                prompt = "Hello, Claude!"
                session_context = {"user_role": "guest"}
                
                results = []
                async for msg in chat_stream(prompt, session_context):
                    results.append(msg)
                
                # 应该返回错误消息
                assert len(results) == 1
                assert results[0]["type"] == "error"
                assert "ANTHROPIC_API_KEY" in results[0]["error"]
    
    def test_estimate_cost_function(self):
        """测试成本估算函数"""
        # 测试零 token
        cost = _estimate_cost(0, 0)
        assert cost == 0.0
        
        # 测试正常 token 数量
        cost = _estimate_cost(1000, 500)
        expected = 1000 * (3.00 / 1_000_000) + 500 * (15.00 / 1_000_000)
        assert abs(cost - expected) < 0.0001
        
        # 测试大量 token
        cost = _estimate_cost(1_000_000, 0)
        assert abs(cost - 3.00) < 0.01
        
        cost = _estimate_cost(0, 1_000_000)
        assert abs(cost - 15.00) < 0.01


class TestMessageFormat:
    """消息格式测试"""
    
    def test_message_format_compliance(self):
        """验证输出消息格式符合 qoder.py 规范"""
        # 测试 _mock_response 返回的消息格式
        messages = []
        async def collect_messages():
            async for msg in _mock_response("test"):
                messages.append(msg)
        
        asyncio.run(collect_messages())
        
        # 验证所有消息都有正确的格式
        for msg in messages:
            assert "type" in msg
            
            if msg["type"] == "text":
                assert "content" in msg
                assert isinstance(msg["content"], str)
                
            elif msg["type"] == "tool_call":
                assert "id" in msg
                assert "tool" in msg
                assert "input" in msg
                
            elif msg["type"] == "tool_result":
                assert "tool_use_id" in msg
                assert "content" in msg
                assert "is_error" in msg
                
            elif msg["type"] == "result":
                assert "subtype" in msg
                assert msg["subtype"] == "complete"
                assert "usage" in msg
                assert isinstance(msg["usage"], dict)
                assert "total_cost_usd" in msg
                
    def test_build_messages_function(self):
        """测试 _build_messages 函数"""
        # 测试空历史
        messages = _build_messages([], "Hello")
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        
        # 测试带历史的构建
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help?"}
        ]
        messages = _build_messages(history, "What can you do?")
        assert len(messages) == 3  # 2历史 + 1当前
        
        # 测试复杂的助理消息（带工具调用）
        history = [
            {"role": "user", "content": "Run a command"},
            {"role": "assistant", "content": [
                {"type": "text", "content": "I'll run that"},
                {"type": "tool_call", "id": "1", "tool": "Bash", "input": {"command": "ls"}}
            ]}
        ]
        messages = _build_messages(history, "What's next?")
        # 应该正确转换工具调用
        
    def test_build_tools_function(self):
        """测试 _build_tools 函数"""
        # 测试空工具列表
        tools = _build_tools([])
        assert tools == []
        
        # 测试已知工具
        tools = _build_tools(["Bash", "Write"])
        assert len(tools) == 2
        
        # 验证工具结构
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            
        # 测试未知工具
        tools = _build_tools(["UnknownTool"])
        assert tools == []  # 未知工具应该被过滤掉


class TestStreamingResponse:
    """流式响应测试"""
    
    @pytest.mark.asyncio
    async def test_async_iterator_return(self):
        """验证 AsyncIterator 返回"""
        prompt = "Test"
        session_context = {}
        
        # 测试模拟模式
        with patch('claw_gateway.services.claude_runtime.ANTHROPIC_AVAILABLE', False):
            stream = chat_stream(prompt, session_context)
            
            # 验证是异步迭代器
            assert hasattr(stream, '__aiter__')
            assert hasattr(stream, '__anext__')
            
            # 验证可以迭代
            count = 0
            async for _ in stream:
                count += 1
                if count > 5:  # 防止无限循环
                    break
            assert count > 0
    
    @pytest.mark.asyncio
    async def test_message_chunking(self):
        """验证消息分块"""
        # 测试模拟响应的分块
        messages = []
        async for msg in _mock_response("test message"):
            messages.append(msg)
            # 模拟延迟
            await asyncio.sleep(0.01)
        
        # 验证有多个分块
        assert len(messages) >= 4  # 至少应该有多个文本块
        
        # 验证分块类型
        text_count = sum(1 for msg in messages if msg["type"] == "text")
        assert text_count >= 3  # 至少3个文本分块
    
    @pytest.mark.asyncio
    async def test_event_conversion(self):
        """测试事件转换函数"""
        # 模拟各种 Claude 事件类型
        mock_events = [
            # content_block_start - text
            MagicMock(
                type="content_block_start",
                content_block=MagicMock(
                    type="text",
                    text="Hello"
                )
            ),
            # content_block_start - tool_use
            MagicMock(
                type="content_block_start",
                content_block=MagicMock(
                    type="tool_use",
                    id="tool_123",
                    name="Bash",
                    input={"command": "ls"}
                )
            ),
            # content_block_delta - text_delta
            MagicMock(
                type="content_block_delta",
                delta=MagicMock(
                    type="text_delta",
                    text=" world"
                )
            ),
            # message_start (应该返回 None)
            MagicMock(type="message_start"),
            # message_delta with stop_reason
            MagicMock(
                type="message_delta",
                delta=MagicMock(
                    stop_reason="end_turn"
                )
            ),
            # message_stop (应该返回 None)
            MagicMock(type="message_stop"),
        ]
        
        for event in mock_events:
            result = _convert_event(event)
            
            if event.type in ["message_start", "message_stop"]:
                assert result is None
            elif event.type == "content_block_start":
                assert result is not None
                if event.content_block.type == "text":
                    assert result["type"] == "text"
                elif event.content_block.type == "tool_use":
                    assert result["type"] == "tool_call"
            elif event.type == "content_block_delta":
                assert result is not None
                assert result["type"] == "text"
            elif event.type == "message_delta" and hasattr(event.delta, 'stop_reason'):
                assert result is not None
                assert result["type"] == "result"
                assert result["stop_reason"] == "end_turn"


class TestSessionContext:
    """会话上下文测试"""
    
    @pytest.mark.asyncio
    async def test_session_context_parameter_handling(self):
        """验证 session_context 参数处理"""
        prompt = "Test context"
        
        # 测试基本 session_context
        session_context = {
            "user_role": "admin",
            "user_id": "12345",
            "allowed_tools": ["Bash", "Write"]
        }
        
        with patch('claw_gateway.services.claude_runtime.ANTHROPIC_AVAILABLE', False):
            results = []
            async for msg in chat_stream(prompt, session_context):
                results.append(msg)
            
            # 验证正确处理了 session_context
            assert len(results) > 0
            # 模拟模式应该能处理任意 session_context
    
    @pytest.mark.asyncio
    async def test_message_history_integration(self):
        """验证 message_history 整合"""
        prompt = "What's next?"
        
        # 测试带历史消息的 session_context
        session_context = {
            "message_history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"},
                {"role": "assistant", "content": "I'm doing well, thanks!"}
            ]
        }
        
        # 验证 _build_messages 正确处理历史
        messages = _build_messages(session_context["message_history"], prompt)
        
        assert len(messages) == 5  # 4历史 + 1当前
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"
        assert messages[-1]["content"] == prompt
    
    @pytest.mark.asyncio
    async def test_allowed_tools_context(self):
        """测试 allowed_tools 上下文处理"""
        prompt = "Use a tool"
        
        # 测试不同的工具权限
        test_cases = [
            {"allowed_tools": []},  # 无工具权限
            {"allowed_tools": ["Read"]},  # 只读权限
            {"allowed_tools": ["Bash", "Write", "Edit", "WebSearch"]},  # 完整权限
        ]
        
        for session_context in test_cases:
            with patch('claw_gateway.services.claude_runtime.ANTHROPIC_AVAILABLE', False):
                results = []
                async for msg in chat_stream(prompt, session_context):
                    results.append(msg)
                
                # 验证模拟响应能处理不同工具权限
                assert len(results) > 0
                # 检查是否有工具调用（模拟模式中会包含工具调用）
                has_tool_call = any(msg["type"] == "tool_call" for msg in results)
                # 模拟模式总是包含工具调用，无论权限


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_chat_stream_with_mocks(self):
        """使用 mock 测试完整的 chat_stream 流程"""
        prompt = "Hello, can you help me?"
        session_context = {
            "user_role": "admin",
            "allowed_tools": ["Bash", "Write"],
            "message_history": [
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"}
            ]
        }
        
        # Mock 完整的 Anthropic SDK 调用流程
        with patch('claw_gateway.services.claude_runtime.ANTHROPIC_AVAILABLE', True):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
                with patch('claw_gateway.services.claude_runtime.Anthropic') as MockAnthropic:
                    # 创建模拟客户端
                    mock_client = MagicMock()
                    MockAnthropic.return_value = mock_client
                    
                    # 创建模拟流
                    mock_stream = MagicMock()
                    
                    # 模拟事件序列
                    events = [
                        MagicMock(type="content_block_start", content_block=MagicMock(
                            type="text", text="Hello"
                        )),
                        MagicMock(type="content_block_delta", delta=MagicMock(
                            type="text_delta", text=" there"
                        )),
                        MagicMock(type="message_delta", delta=MagicMock(
                            stop_reason="end_turn"
                        )),
                    ]
                    
                    # 设置流的行为
                    mock_stream.__iter__.return_value = iter(events)
                    mock_stream.get_final_message.return_value = MagicMock(
                        usage=MagicMock(input_tokens=10, output_tokens=5)
                    )
                    
                    # 设置上下文管理器
                    mock_client.messages.stream.return_value.__enter__.return_value = mock_stream
                    mock_client.messages.stream.return_value.__exit__.return_value = None
                    
                    # 调用被测试函数
                    results = []
                    async for msg in chat_stream(prompt, session_context):
                        results.append(msg)
                    
                    # 验证结果
                    assert len(results) >= 3
                    
                    # 验证消息类型
                    types = [msg["type"] for msg in results]
                    assert "text" in types
                    assert "result" in types
                    
                    # 验证最终结果包含使用统计
                    final_result = next(msg for msg in results if msg["type"] == "result")
                    assert "usage" in final_result
                    assert "total_cost_usd" in final_result
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        prompt = "Test error"
        session_context = {}
        
        # 测试 SDK 调用异常
        with patch('claw_gateway.services.claude_runtime.ANTHROPIC_AVAILABLE', True):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
                with patch('claw_gateway.services.claude_runtime.Anthropic') as MockAnthropic:
                    mock_client = MagicMock()
                    MockAnthropic.return_value = mock_client
                    
                    # 模拟异常
                    mock_client.messages.stream.side_effect = Exception("API Error")
                    
                    results = []
                    async for msg in chat_stream(prompt, session_context):
                        results.append(msg)
                    
                    # 应该返回错误消息
                    assert len(results) == 1
                    assert results[0]["type"] == "error"
                    assert "API Error" in results[0]["error"]


if __name__ == "__main__":
    # 简单运行测试
    import sys
    sys.exit(pytest.main([__file__, "-v"]))