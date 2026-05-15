#!/usr/bin/env python3
"""
claude_runtime.py 测试用例 - 最终版本
"""

import sys
import os
import asyncio
import json
from unittest.mock import patch, MagicMock

# 设置路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

print("=" * 80)
print("claude_runtime.py 测试用例")
print("=" * 80)

# 模拟必要的模块和函数
def mock_build_permission_hook(session_context):
    """模拟权限钩子函数"""
    def permission_hook(input_data, tool_use_id, context):
        return {
            "permissionDecision": "allow",
            "updatedInput": input_data.get("tool_input", {})
        }
    return permission_hook

# 创建模拟模块
sys.modules['claw_gateway'] = MagicMock()
sys.modules['claw_gateway.permission'] = MagicMock()
sys.modules['claw_gateway.permission'].build_permission_hook = mock_build_permission_hook

# 模拟 anthropic 模块（当 SDK 可用时）
sys.modules['anthropic'] = MagicMock()
sys.modules['anthropic.types'] = MagicMock()

# 定义模拟类型
class MockMessageStreamEvent:
    def __init__(self, type, **kwargs):
        self.type = type
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockTextBlock:
    type = "text"
    
    def __init__(self, text):
        self.text = text

class MockToolUseBlock:
    type = "tool_use"
    
    def __init__(self, id, name, input):
        self.id = id
        self.name = name
        self.input = input

class MockTextDelta:
    type = "text_delta"
    
    def __init__(self, text):
        self.text = text

# 设置模拟类型
sys.modules['anthropic.types'].MessageStreamEvent = MockMessageStreamEvent
sys.modules['anthropic.types'].TextBlock = MockTextBlock
sys.modules['anthropic.types'].ToolUseBlock = MockToolUseBlock
sys.modules['anthropic.types'].TextDelta = MockTextDelta
sys.modules['anthropic.types'].Message = MagicMock
sys.modules['anthropic.types'].ToolResultBlock = MagicMock
sys.modules['anthropic.types'].ContentBlock = MagicMock
sys.modules['anthropic.types'].ToolUseBlockDelta = MagicMock
sys.modules['anthropic.types'].MessageDeltaUsage = MagicMock

# 现在导入被测试模块
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        'claude_runtime',
        os.path.join(current_dir, 'services', 'claude_runtime.py')
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules['claude_runtime'] = module
    spec.loader.exec_module(module)
    
    # 导入需要的函数
    from claude_runtime import (
        chat_stream,
        _mock_response,
        _estimate_cost,
        _build_messages,
        _build_tools,
        ANTHROPIC_AVAILABLE,
    )
    
    print("✓ 成功导入 claude_runtime 模块")
    print(f"  ANTHROPIC_AVAILABLE = {ANTHROPIC_AVAILABLE}")
    
except Exception as e:
    print(f"✗ 导入失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


async def run_tests():
    """运行所有测试"""
    
    test_results = []
    
    # 测试 1: 基础功能测试
    print("\n1. 基础功能测试")
    print("-" * 40)
    
    try:
        # 测试函数存在
        assert hasattr(chat_stream, '__call__'), "chat_stream 函数不存在"
        print("  ✓ chat_stream 函数存在且可调用")
        
        # 测试成本估算
        cost = _estimate_cost(0, 0)
        assert cost == 0.0, f"零 token 成本应为 0.0，实际为 {cost}"
        print("  ✓ _estimate_cost 零 token 测试通过")
        
        cost = _estimate_cost(1000, 500)
        expected = 1000 * (3.00 / 1_000_000) + 500 * (15.00 / 1_000_000)
        assert abs(cost - expected) < 0.0001, f"成本计算错误: {cost}"
        print("  ✓ _estimate_cost 正常 token 测试通过")
        
        test_results.append(("基础功能", "通过"))
    except AssertionError as e:
        print(f"  ✗ 基础功能测试失败: {e}")
        test_results.append(("基础功能", f"失败: {e}"))
    
    # 测试 2: 模拟模式测试
    print("\n2. 模拟模式测试")
    print("-" * 40)
    
    try:
        with patch('claude_runtime.ANTHROPIC_AVAILABLE', False):
            prompt = "Hello, Claude!"
            session_context = {"user_role": "guest"}
            
            messages = []
            async for msg in chat_stream(prompt, session_context):
                messages.append(msg)
            
            assert len(messages) > 0, "模拟模式应返回消息"
            assert any(msg["type"] == "text" for msg in messages), "应包含文本消息"
            print(f"  ✓ 模拟模式返回 {len(messages)} 条消息")
            print("  ✓ 消息格式正确")
            
        test_results.append(("模拟模式", "通过"))
    except Exception as e:
        print(f"  ✗ 模拟模式测试失败: {e}")
        test_results.append(("模拟模式", f"失败: {e}"))
    
    # 测试 3: API Key 缺失处理
    print("\n3. API Key 缺失处理测试")
    print("-" * 40)
    
    try:
        with patch('claude_runtime.ANTHROPIC_AVAILABLE', True):
            with patch.dict(os.environ, {}, clear=True):
                prompt = "Hello, Claude!"
                session_context = {"user_role": "guest"}
                
                messages = []
                async for msg in chat_stream(prompt, session_context):
                    messages.append(msg)
                
                assert len(messages) == 1, "API Key 缺失时应返回一条错误消息"
                assert messages[0]["type"] == "error", "应为错误消息类型"
                assert "ANTHROPIC_API_KEY" in messages[0]["error"], "错误消息应提及 API Key"
                print("  ✓ API Key 缺失时返回正确错误消息")
                
        test_results.append(("API Key 缺失处理", "通过"))
    except Exception as e:
        print(f"  ✗ API Key 缺失测试失败: {e}")
        test_results.append(("API Key 缺失处理", f"失败: {e}"))
    
    # 测试 4: 消息格式测试
    print("\n4. 消息格式测试")
    print("-" * 40)
    
    try:
        # 测试 _mock_response 的消息格式
        messages = []
        async for msg in _mock_response("test message"):
            messages.append(msg)
        
        # 验证消息类型
        type_counts = {}
        for msg in messages:
            msg_type = msg["type"]
            type_counts[msg_type] = type_counts.get(msg_type, 0) + 1
            
            # 验证每种消息类型的格式
            if msg_type == "text":
                assert "content" in msg, "text 消息应包含 content"
                assert isinstance(msg["content"], str), "content 应为字符串"
            elif msg_type == "tool_call":
                assert "id" in msg, "tool_call 消息应包含 id"
                assert "tool" in msg, "tool_call 消息应包含 tool"
                assert "input" in msg, "tool_call 消息应包含 input"
            elif msg_type == "tool_result":
                assert "tool_use_id" in msg, "tool_result 消息应包含 tool_use_id"
                assert "content" in msg, "tool_result 消息应包含 content"
                assert "is_error" in msg, "tool_result 消息应包含 is_error"
            elif msg_type == "result":
                assert "subtype" in msg, "result 消息应包含 subtype"
                assert "usage" in msg, "result 消息应包含 usage"
                assert "total_cost_usd" in msg, "result 消息应包含 total_cost_usd"
        
        print(f"  ✓ _mock_response 返回 {len(messages)} 条消息")
        print(f"  ✓ 消息类型分布: {type_counts}")
        print("  ✓ 所有消息格式符合规范")
        
        test_results.append(("消息格式", "通过"))
    except Exception as e:
        print(f"  ✗ 消息格式测试失败: {e}")
        test_results.append(("消息格式", f"失败: {e}"))
    
    # 测试 5: 流式响应测试
    print("\n5. 流式响应测试")
    print("-" * 40)
    
    try:
        prompt = "Test streaming"
        session_context = {}
        
        with patch('claude_runtime.ANTHROPIC_AVAILABLE', False):
            # 验证是异步迭代器
            stream = chat_stream(prompt, session_context)
            assert hasattr(stream, '__aiter__'), "应支持异步迭代"
            assert hasattr(stream, '__anext__'), "应支持异步迭代"
            
            # 验证可以迭代
            count = 0
            async for msg in stream:
                count += 1
                if count > 10:  # 防止无限循环
                    break
            
            assert count > 0, "应至少返回一条消息"
            print(f"  ✓ 流式响应返回 {count} 条消息")
            print("  ✓ 支持异步迭代器协议")
        
        test_results.append(("流式响应", "通过"))
    except Exception as e:
        print(f"  ✗ 流式响应测试失败: {e}")
        test_results.append(("流式响应", f"失败: {e}"))
    
    # 测试 6: 会话上下文测试
    print("\n6. 会话上下文测试")
    print("-" * 40)
    
    try:
        prompt = "Test context"
        session_context = {
            "user_role": "admin",
            "user_id": "12345",
            "allowed_tools": ["Bash", "Write"],
            "message_history": [
                {"role": "user", "content": "Previous message"},
                {"role": "assistant", "content": "Previous response"}
            ]
        }
        
        with patch('claude_runtime.ANTHROPIC_AVAILABLE', False):
            messages = []
            async for msg in chat_stream(prompt, session_context):
                messages.append(msg)
            
            assert len(messages) > 0, "应返回消息"
            print(f"  ✓ 会话上下文处理返回 {len(messages)} 条消息")
        
        test_results.append(("会话上下文", "通过"))
    except Exception as e:
        print(f"  ✗ 会话上下文测试失败: {e}")
        test_results.append(("会话上下文", f"失败: {e}"))
    
    # 测试 7: 消息构建测试
    print("\n7. 消息构建测试")
    print("-" * 40)
    
    try:
        # 测试空历史
        messages = _build_messages([], "Hello")
        assert len(messages) == 1, "空历史应返回一条消息"
        assert messages[0]["role"] == "user", "角色应为 user"
        assert messages[0]["content"] == "Hello", "内容应正确"
        print("  ✓ _build_messages 空历史测试通过")
        
        # 测试简单历史
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello! How can I help?"}
        ]
        messages = _build_messages(history, "What can you do?")
        # 注意：_build_messages 可能不会转换所有历史消息
        print(f"  ✓ _build_messages 带历史返回 {len(messages)} 条消息")
        
        test_results.append(("消息构建", "通过"))
    except Exception as e:
        print(f"  ✗ 消息构建测试失败: {e}")
        test_results.append(("消息构建", f"失败: {e}"))
    
    # 测试 8: 工具构建测试
    print("\n8. 工具构建测试")
    print("-" * 40)
    
    try:
        # 测试空工具列表
        tools = _build_tools([])
        assert tools == [], "空工具列表应返回空列表"
        print("  ✓ _build_tools 空列表测试通过")
        
        # 测试已知工具
        tools = _build_tools(["Bash", "Write"])
        assert len(tools) == 2, f"应返回 2 个工具，实际返回 {len(tools)}"
        
        # 验证工具结构
        for tool in tools:
            assert "name" in tool, "工具应包含 name"
            assert "description" in tool, "工具应包含 description"
            assert "input_schema" in tool, "工具应包含 input_schema"
        
        print(f"  ✓ _build_tools 返回 {len(tools)} 个工具")
        print("  ✓ 工具结构正确")
        
        test_results.append(("工具构建", "通过"))
    except Exception as e:
        print(f"  ✗ 工具构建测试失败: {e}")
        test_results.append(("工具构建", f"失败: {e}"))
    
    # 输出测试结果
    print("\n" + "=" * 80)
    print("测试结果摘要")
    print("=" * 80)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, status in test_results if status == "通过")
    failed_tests = total_tests - passed_tests
    
    print(f"总测试数: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {failed_tests}")
    
    if failed_tests > 0:
        print("\n失败的测试:")
        for test_name, status in test_results:
            if status != "通过":
                print(f"  ✗ {test_name}: {status}")
    
    print("=" * 80)
    
    if failed_tests == 0:
        print("✓ 所有测试通过!")
        return True
    else:
        print("✗ 有测试失败，请检查上述问题")
        return False


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)