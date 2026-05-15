#!/bin/bash

echo "=== Claw Agent v2 UI前端测试运行脚本 ==="
echo ""

# 检查是否在正确目录
if [ ! -f "package.json" ]; then
    echo "错误：请在claw-ui目录下运行此脚本"
    exit 1
fi

echo "1. 安装依赖（如果尚未安装）"
npm install

echo ""
echo "2. 运行组件测试"
echo "----------------------------------------"
npx vitest run src/components/__tests__/ChatWindow.test.tsx
echo ""
npx vitest run src/components/__tests__/MessageBubble.test.tsx
echo ""
npx vitest run src/components/__tests__/InputBox.test.tsx

echo ""
echo "3. 运行Hook测试"
echo "----------------------------------------"
npx vitest run src/hooks/__tests__/useChat.test.ts

echo ""
echo "4. 运行集成测试"
echo "----------------------------------------"
npx vitest run src/components/__tests__/integration.test.tsx

echo ""
echo "5. 运行所有测试（汇总）"
echo "----------------------------------------"
npx vitest run

echo ""
echo "=== 测试完成 ==="
echo "测试报告已生成在飞书云文档：https://www.feishu.cn/docx/K5eEdpb5qouGSyxin5lcS4Xrnwe"
echo "如需查看测试覆盖率，请运行：npm run test:coverage"