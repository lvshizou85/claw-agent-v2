#!/usr/bin/env python3
"""
简化的 claude_runtime 测试
"""

import sys
import os
import asyncio
import pytest
from unittest.mock import patch, MagicMock

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模拟 permission 模块
class MockPermission:
    @staticmethod
    def build_permission_hook(context):
        return lambda x: x

# 创建模拟模块
sys.modules['claw_gateway'] = MagicMock()
sys.modules['claw_gateway.permission'] = MockPermission()

# 模拟 Anthropic 类型（当 SDK 不可用时）
class MockMessageStreamEvent:
    type = "mock_event"

class MockTextBlock:
    type = "text"
    text = "mock text"

class MockToolUseBlock:
    type = "tool_use"
    id = "mock_id"
    name = "mock_tool"
    input = {}

class MockTextDelta:
    type = "text_delta"
    text = "mock delta"

# 创建模拟的 anthropic 模块
sys.modules['anthropic'] = MagicMock()
sys.modules['anthropic.types'] = MagicMock()
sys.modules['anthropic.types'].MessageStreamEvent = MockMessageStreamEvent
sys.modules['anthropic.types'].TextBlock = MockTextBlock
sys.modules['anthropic.types'].ToolUseBlock = MockToolUseBlock
sys.modules['anthropic.types'].TextDelta = MockTextDelta

# 现在导入 claude_runtime
try:
    from services.claude_runtime import (
        chat_stream,
        _mock_response,
        _estimate_cost,
        _build_messages,
        _build_tools,
        _convert_event,
        ANTHROPIC_AVAILABLE,
    )
    print("✓ 成功导入 claude_runtime 模块")
    print(f"  ANTHROPIC_AVAILABLE = {ANTHROPIC_AVAILABLE}")
except ImportError as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


async def test_basic_functionality():
    """测试基础功能"""
    print("\n1. 测试基础功能")
    
    # 测试函数存在
    assert hasattr(chat_stream, '__call__')
    # chat_stream 是一个返回异步生成器的函数，不是协程函数
    print("  ✓ chat_stream 函数存在且可调用")
    
    # 测试成本估算
    cost = _estimate_cost(0, 0)
    assert cost == 0.0
    print("  ✓ _estimate_cost 零 token 测试通过")
    
    cost = _estimate_cost(1000, 500)
    expected = 1000 * (3.00 / 1_000_000) + 500 * (15.00 / 1_000_000)
    assert abs(cost - expected) < 0.0001
    print("  ✓ _estimate_cost 正常 token 测试通过")
    
    return True


async def test_mock_response():
    """测试模拟响应"""
    print("\n2. 测试模拟响应")
    
    messages = []
    async for msg in _mock_response("test message"):
        messages.append(msg)
    
    assert len(messages) > 0
    print(f"  ✓ _mock_response 返回 {len(messages)} 条消息")
    
    # 验证消息格式
    for msg in messages:
        assert "type" in msg
        assert msg["type"] in ["text", "tool_call", "tool_result", "result"]
    
    print("  ✓ 所有消息格式正确")
    
    return True


async def test_message_building():
    """测试消息构建"""
    print("\n3. 测试消息构建")
    
    # 测试空历史
    messages = _build_messages([], "Hello")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    print("  ✓ _build_messages 空历史测试通过")
    
    # 测试带历史的构建
    history = [
        {"role": "user", "content": "Hi"},
        {"role": "assistant", "content": "Hello! How can I help?"}
    ]
    messages = _build_messages(history, "What can you do?")
    assert len(messages) == 3
    print("  ✓ _build_messages 带历史测试通过")
    
    return True


async def test_tool_building():
    """测试工具构建"""
    print("\n4. 测试工具构建")
    
    # 测试空工具列表
    tools = _build_tools([])
    assert tools == []
    print("  ✓ _build_tools 空列表测试通过")
    
    # 测试已知工具
    tools = _build_tools(["Bash", "Write"])
    assert len(tools) == 2
    print(f"  ✓ _build_tools 返回 {len(tools)} 个工具")
    
    # 验证工具结构
    for tool in tools:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
    print("  ✓ 工具结构正确")
    
    return True


async def test_simulated_mode():
    """测试模拟模式"""
    print("\n5. 测试模拟模式")
    
    # 模拟 ANTHROPIC_AVAILABLE = False
    with patch('services.claude_runtime.ANTHROPIC_AVAILABLE', False):
        prompt = "Hello, Claude!"
        session_context = {"user_role": "guest"}
        
        messages = []
        async for msg in chat_stream(prompt, session_context):
            messages.append(msg)
        
        assert len(messages) > 0
        print(f"  ✓ 模拟模式返回 {len(messages)} 条消息")
        
        # 验证至少有一条消息
        assert any(msg["type"] == "text" for msg in messages)
        print("  ✓ 包含文本消息")
    
    return True


async def test_api_key_missing():
    """测试 API Key 缺失处理"""
    print("\n6. 测试 API Key 缺失处理")
    
    # 模拟 SDK 可用但无 API Key
    with patch('services.claude_runtime.ANTHROPIC_AVAILABLE', True):
        with patch.dict(os.environ, {}, clear=True):
            prompt = "Hello, Claude!"
            session_context = {"user_role": "guest"}
            
            messages = []
            async for msg in chat_stream(prompt, session_context):
                messages.append(msg)
            
            assert len(messages) == 1
            assert messages[0]["type"] == "error"
            assert "ANTHROPIC_API_KEY" in messages[0]["error"]
            print("  ✓ API Key 缺失时返回正确错误消息")
    
    return True


async def test_session_context():
    """测试会话上下文"""
    print("\n7. 测试会话上下文")
    
    prompt = "Test context"
    session_context = {
        "user_role": "admin",
        "user_id": "12345",
        "allowed_tools": ["Bash", "Write"],
        "message_history": [
            {"role": "user", "content": "Previous"},
            {"role": "assistant", "content": "Response"}
        ]
    }
    
    with patch('services.claude_runtime.ANTHROPIC_AVAILABLE', False):
        messages = []
        async for msg in chat_stream(prompt, session_context):
            messages.append(msg)
        
        assert len(messages) > 0
        print(f"  ✓ 会话上下文处理返回 {len(messages)} 条消息")
    
    return True


async def run_all_tests():
    """运行所有测试"""
    print("=" * 80)
    print("开始运行 claude_runtime 测试")
    print("=" * 80)
    
    tests = [
        ("基础功能", test_basic_functionality),
        ("模拟响应", test_mock_response),
        ("消息构建", test_message_building),
        ("工具构建", test_tool_building),
        ("模拟模式", test_simulated_mode),
        ("API Key 缺失", test_api_key_missing),
        ("会话上下文", test_session_context),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
            else:
                failed += 1
                print(f"  ✗ {test_name} 测试失败")
        except Exception as e:
            failed += 1
            print(f"  ✗ {test_name} 测试异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试结果摘要")
    print("=" * 80)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print("=" * 80)
    
    if failed == 0:
        print("✓ 所有测试通过!")
        return True
    else:
        print("✗ 有测试失败")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)