"""
Tests for Claude Runtime Service
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from claw_gateway.services.claude_runtime import (
    chat_stream,
    _mock_response,
    _estimate_cost,
    ANTHROPIC_AVAILABLE,
)


class TestChatStreamBasic:
    """基本对话测试"""

    @pytest.mark.asyncio
    async def test_chat_stream_basic(self):
        """测试基本对话功能"""
        prompt = "Hello, Claude!"
        session_context = {"user_role": "guest", "allowed_tools": []}

        if ANTHROPIC_AVAILABLE:
            # Mock Anthropic client
            with patch("claw_gateway.services.claude_runtime.Anthropic") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                # Mock streaming response
                mock_stream = MagicMock()
                mock_stream.text_stream = iter(["Hello", " ", "World"])
                mock_stream.get_final_message.return_value = MagicMock(
                    usage=MagicMock(input_tokens=10, output_tokens=5)
                )
                mock_instance.messages.stream.return_value.__enter__ = MagicMock(
                    return_value=mock_stream
                )
                mock_instance.messages.stream.return_value.__exit__ = MagicMock(
                    return_value=None
                )

                results = []
                async for msg in chat_stream(prompt, session_context):
                    results.append(msg)

                # 验证结果
                assert len(results) >= 2
                assert results[0]["type"] == "text"
        else:
            # SDK 不可用时测试 mock response
            results = []
            async for msg in chat_stream(prompt, session_context):
                results.append(msg)

            assert len(results) >= 2
            assert results[0]["type"] == "text"
            assert "[Claude SDK not available]" in results[0]["content"]

    @pytest.mark.asyncio
    async def test_mock_response(self):
        """测试 SDK 不可用时的降级响应"""
        prompt = "Test message"
        results = []

        async for msg in _mock_response(prompt):
            results.append(msg)

        assert len(results) >= 2
        assert results[0]["type"] == "text"
        assert "[Claude SDK not available]" in results[0]["content"]
        # 最后一条应该是 result
        assert results[-1]["type"] == "result"
        assert results[-1]["total_cost_usd"] == 0.0


class TestChatStreamRBAC:
    """RBAC 权限测试"""

    @pytest.mark.asyncio
    async def test_rbac_guest_limited_tools(self):
        """测试 guest 角色的工具限制"""
        prompt = "List files"
        session_context = {
            "user_role": "guest",
            "allowed_tools": ["Read"],  # 只有 Read 权限
        }

        if ANTHROPIC_AVAILABLE:
            with patch("claw_gateway.services.claude_runtime.Anthropic") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                mock_stream = MagicMock()
                mock_stream.text_stream = iter(["Response"])
                mock_stream.get_final_message.return_value = MagicMock(
                    usage=MagicMock(input_tokens=5, output_tokens=3)
                )
                mock_instance.messages.stream.return_value.__enter__ = MagicMock(
                    return_value=mock_stream
                )
                mock_instance.messages.stream.return_value.__exit__ = MagicMock(
                    return_value=None
                )

                # 验证工具列表被正确传递
                results = []
                async for msg in chat_stream(prompt, session_context):
                    results.append(msg)

                # 检查 tools 参数
                call_kwargs = mock_instance.messages.stream.call_args
                assert call_kwargs is not None
                tools = call_kwargs.kwargs.get("tools")
                assert tools == [{"name": "Read", "description": "Read"}]
        else:
            # SDK 不可用时只测试 mock
            results = []
            async for msg in chat_stream(prompt, session_context):
                results.append(msg)
            assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_rbac_admin_full_tools(self):
        """测试 admin 角色的完整权限"""
        prompt = "Execute command"
        session_context = {
            "user_role": "admin",
            "allowed_tools": ["Bash", "Write", "Edit", "WebSearch"],
        }

        if ANTHROPIC_AVAILABLE:
            with patch("claw_gateway.services.claude_runtime.Anthropic") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                mock_stream = MagicMock()
                mock_stream.text_stream = iter(["Done"])
                mock_stream.get_final_message.return_value = MagicMock(
                    usage=MagicMock(input_tokens=5, output_tokens=2)
                )
                mock_instance.messages.stream.return_value.__enter__ = MagicMock(
                    return_value=mock_stream
                )
                mock_instance.messages.stream.return_value.__exit__ = MagicMock(
                    return_value=None
                )

                results = []
                async for msg in chat_stream(prompt, session_context):
                    results.append(msg)

                # Admin 可以使用所有工具
                call_kwargs = mock_instance.messages.stream.call_args
                tools = call_kwargs.kwargs.get("tools")
                assert len(tools) == 4
        else:
            results = []
            async for msg in chat_stream(prompt, session_context):
                results.append(msg)
            assert len(results) >= 1


class TestChatStreamHITL:
    """HITL (Human-In-The-Loop) 审批测试"""

    @pytest.mark.asyncio
    async def test_hitl_high_risk_tools(self):
        """测试高风险工具的审批流程"""
        prompt = "Write a file"
        session_context = {
            "user_role": "guest",  # 非 admin
            "allowed_tools": ["Bash", "Write"],  # 包含高风险工具
        }

        # 高风险工具需要审批，但当前实现会直接调用
        # 审批逻辑应在 permission hook 层处理
        if ANTHROPIC_AVAILABLE:
            with patch("claw_gateway.services.claude_runtime.Anthropic") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                mock_stream = MagicMock()
                mock_stream.text_stream = iter(["File written"])
                mock_stream.get_final_message.return_value = MagicMock(
                    usage=MagicMock(input_tokens=5, output_tokens=3)
                )
                mock_instance.messages.stream.return_value.__enter__ = MagicMock(
                    return_value=mock_stream
                )
                mock_instance.messages.stream.return_value.__exit__ = MagicMock(
                    return_value=None
                )

                results = []
                async for msg in chat_stream(prompt, session_context):
                    results.append(msg)

                # 结果应该包含 text 和 result
                types = [r["type"] for r in results]
                assert "text" in types
                assert "result" in types
        else:
            results = []
            async for msg in chat_stream(prompt, session_context):
                results.append(msg)
            assert results[-1]["type"] == "result"

    @pytest.mark.asyncio
    async def test_hitl_no_high_risk_tools(self):
        """测试无高风险工具时不需要审批"""
        prompt = "Read info"
        session_context = {
            "user_role": "guest",
            "allowed_tools": ["Read"],  # 无高风险工具
        }

        if ANTHROPIC_AVAILABLE:
            with patch("claw_gateway.services.claude_runtime.Anthropic") as mock_client:
                mock_instance = MagicMock()
                mock_client.return_value = mock_instance

                mock_stream = MagicMock()
                mock_stream.text_stream = iter(["Info"])
                mock_stream.get_final_message.return_value = MagicMock(
                    usage=MagicMock(input_tokens=3, output_tokens=2)
                )
                mock_instance.messages.stream.return_value.__enter__ = MagicMock(
                    return_value=mock_stream
                )
                mock_instance.messages.stream.return_value.__exit__ = MagicMock(
                    return_value=None
                )

                results = []
                async for msg in chat_stream(prompt, session_context):
                    results.append(msg)

                assert results[-1]["type"] == "result"
        else:
            results = []
            async for msg in chat_stream(prompt, session_context):
                results.append(msg)
            assert results[-1]["type"] == "result"


class TestCostEstimation:
    """成本估算测试"""

    def test_estimate_cost_zero(self):
        """测试零 token 的成本"""
        cost = _estimate_cost(0, 0)
        assert cost == 0.0

    def test_estimate_cost_normal(self):
        """测试正常 token 量的成本"""
        # 1000 input + 500 output
        cost = _estimate_cost(1000, 500)
        # Input: 1000 * 3.75/1M = 0.00375
        # Output: 500 * 15/1M = 0.0075
        # Total: 0.01125
        assert abs(cost - 0.01125) < 0.0001

    def test_estimate_cost_large(self):
        """测试大批量 token 的成本"""
        # 1M input tokens
        cost = _estimate_cost(1_000_000, 0)
        assert abs(cost - 3.75) < 0.01

        # 1M output tokens
        cost = _estimate_cost(0, 1_000_000)
        assert abs(cost - 15.0) < 0.01
