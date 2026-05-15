#!/usr/bin/env python3
"""
测试 Claude Runtime 实现
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_mock_mode():
    """测试开发模式（无 SDK 安装）"""
    print("=== 测试开发模式 ===")
    
    from claw_gateway.services.claude_runtime import chat_stream
    
    # 模拟会话上下文
    session_context = {
        "user_id": "test_user_001",
        "user_role": "developer",
        "allowed_tools": ["Bash", "Write", "Edit"],
        "message_history": []
    }
    
    # 测试对话
    prompt = "你好，请帮我列出当前目录下的文件"
    
    print(f"发送消息: {prompt}")
    print("接收响应:")
    
    async for msg in chat_stream(prompt, session_context):
        print(f"  -> {msg}")
        
        # 如果是工具调用，模拟工具结果
        if msg.get("type") == "tool_call":
            print(f"  [模拟工具执行] {msg.get('tool')}: {msg.get('input')}")
            # 这里可以模拟工具返回结果
    
    print("\n=== 开发模式测试完成 ===")

async def test_with_sdk():
    """测试实际 SDK 模式"""
    print("=== 测试 SDK 模式 ===")
    
    # 检查环境变量
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("警告: ANTHROPIC_API_KEY 环境变量未设置")
        print("跳过 SDK 模式测试")
        return
    
    try:
        import anthropic
        print(f"找到 Anthropic SDK: {anthropic.__version__}")
    except ImportError:
        print("错误: Anthropic SDK 未安装")
        print("请运行: pip install anthropic")
        return
    
    from claw_gateway.services.claude_runtime import chat_stream
    
    # 模拟会话上下文
    session_context = {
        "user_id": "test_user_001",
        "user_role": "developer",
        "allowed_tools": ["Bash"],
        "message_history": []
    }
    
    # 测试简单对话
    prompt = "你好，请用中文回复"
    
    print(f"发送消息: {prompt}")
    print("接收响应:")
    
    try:
        async for msg in chat_stream(prompt, session_context):
            print(f"  -> {msg}")
    except Exception as e:
        print(f"错误: {e}")
    
    print("\n=== SDK 模式测试完成 ===")

def test_permission_hook():
    """测试权限 Hook"""
    print("=== 测试权限 Hook ===")
    
    from claw_gateway.permission import build_permission_hook
    
    # 测试不同角色的权限
    test_cases = [
        {
            "role": "admin",
            "tool_name": "Bash",
            "expected": "allow"
        },
        {
            "role": "guest", 
            "tool_name": "Bash",
            "expected": "deny"
        },
        {
            "role": "developer",
            "tool_name": "代码审查",
            "expected": "allow"
        }
    ]
    
    for case in test_cases:
        session_context = {
            "user": {
                "role": case["role"]
            }
        }
        
        hook = build_permission_hook(session_context)
        result = hook(
            {"tool_name": case["tool_name"], "tool_input": {}},
            "test_tool_id",
            {}
        )
        
        print(f"角色 {case['role']} 调用 {case['tool_name']}: {result.get('permissionDecision')}")
        assert result.get("permissionDecision") == case["expected"], f"权限检查失败: {result}"
    
    print("=== 权限 Hook 测试完成 ===")

async def main():
    """主测试函数"""
    print("开始测试 Claude Runtime 实现")
    print("=" * 50)
    
    # 测试权限 Hook
    test_permission_hook()
    print()
    
    # 测试开发模式
    await test_mock_mode()
    print()
    
    # 测试 SDK 模式（如果环境配置正确）
    await test_with_sdk()
    
    print("=" * 50)
    print("所有测试完成")

if __name__ == "__main__":
    asyncio.run(main())