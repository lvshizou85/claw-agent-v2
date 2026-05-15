#!/usr/bin/env python3
import sys
import os

# 设置路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# 模拟必要的模块
class MockModule:
    pass

sys.modules['claw_gateway'] = MockModule()
sys.modules['claw_gateway.permission'] = MockModule()
sys.modules['anthropic'] = MockModule()
sys.modules['anthropic.types'] = MockModule()

# 动态导入 claude_runtime
import importlib.util
spec = importlib.util.spec_from_file_location(
    'claude_runtime',
    os.path.join(current_dir, 'services', 'claude_runtime.py')
)
module = importlib.util.module_from_spec(spec)
sys.modules['claude_runtime'] = module

# 执行模块
spec.loader.exec_module(module)

# 测试 _build_messages
print("测试 _build_messages 函数:")
print("-" * 50)

# 测试1: 空历史
print("\n1. 空历史:")
messages = module._build_messages([], "Hello")
print(f"  消息数量: {len(messages)}")
for i, msg in enumerate(messages):
    print(f"  消息 {i}: {msg}")

# 测试2: 简单历史
print("\n2. 简单历史:")
history = [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help?"}
]
messages = module._build_messages(history, "What can you do?")
print(f"  消息数量: {len(messages)}")
for i, msg in enumerate(messages):
    print(f"  消息 {i}: {msg}")

# 测试3: 复杂助理消息
print("\n3. 复杂助理消息（带工具调用）:")
history = [
    {"role": "user", "content": "Run a command"},
    {"role": "assistant", "content": [
        {"type": "text", "content": "I'll run that"},
        {"type": "tool_call", "id": "1", "tool": "Bash", "input": {"command": "ls"}}
    ]}
]
messages = module._build_messages(history, "What's next?")
print(f"  消息数量: {len(messages)}")
for i, msg in enumerate(messages):
    print(f"  消息 {i}: 角色={msg.get('role')}, 内容类型={type(msg.get('content'))}")