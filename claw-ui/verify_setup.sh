#!/bin/bash

echo "=== Claw UI 项目验证脚本 ==="
echo ""

# 检查目录结构
echo "1. 检查目录结构..."
if [ -d "src/components" ] && [ -d "src/hooks" ] && [ -d "src/types" ]; then
    echo "✓ 目录结构完整"
else
    echo "✗ 目录结构不完整"
    exit 1
fi

# 检查关键文件
echo ""
echo "2. 检查关键文件..."
required_files=(
    "package.json"
    "index.html"
    "src/App.tsx"
    "src/main.tsx"
    "src/index.css"
    "vite.config.ts"
    "tailwind.config.js"
    "tsconfig.json"
)

missing_files=0
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file 不存在"
        missing_files=$((missing_files + 1))
    fi
done

if [ $missing_files -gt 0 ]; then
    echo "✗ 缺少 $missing_files 个关键文件"
    exit 1
fi

# 检查 package.json 脚本
echo ""
echo "3. 检查 package.json 脚本..."
if grep -q '"dev"' package.json && grep -q '"build"' package.json; then
    echo "✓ package.json 脚本配置正确"
else
    echo "✗ package.json 脚本配置不完整"
    exit 1
fi

# 检查 TypeScript 配置
echo ""
echo "4. 检查 TypeScript 配置..."
if grep -q '"jsx": "react-jsx"' tsconfig.json; then
    echo "✓ TypeScript React 配置正确"
else
    echo "✗ TypeScript 配置不正确"
    exit 1
fi

# 检查 Vite 配置
echo ""
echo "5. 检查 Vite 配置..."
if grep -q "defineConfig" vite.config.ts && grep -q "react()" vite.config.ts; then
    echo "✓ Vite 配置正确"
else
    echo "✗ Vite 配置不正确"
    exit 1
fi

# 检查 Tailwind 配置
echo ""
echo "6. 检查 Tailwind 配置..."
if grep -q "content" tailwind.config.js; then
    echo "✓ Tailwind 配置正确"
else
    echo "✗ Tailwind 配置不正确"
    exit 1
fi

# 检查组件文件
echo ""
echo "7. 检查组件文件..."
components=("ChatWindow.tsx" "MessageBubble.tsx" "InputBox.tsx")
for component in "${components[@]}"; do
    if [ -f "src/components/$component" ]; then
        echo "✓ src/components/$component"
    else
        echo "✗ src/components/$component 不存在"
        exit 1
    fi
done

# 检查 Hook 文件
echo ""
echo "8. 检查 Hook 文件..."
if [ -f "src/hooks/useChat.ts" ]; then
    echo "✓ src/hooks/useChat.ts"
    if grep -q "sendMessage" src/hooks/useChat.ts && grep -q "isConnecting" src/hooks/useChat.ts; then
        echo "✓ useChat Hook 包含核心功能"
    else
        echo "✗ useChat Hook 功能不完整"
        exit 1
    fi
else
    echo "✗ src/hooks/useChat.ts 不存在"
    exit 1
fi

# 检查环境变量配置
echo ""
echo "9. 检查环境变量配置..."
if [ -f ".env.example" ]; then
    echo "✓ .env.example 文件存在"
    if grep -q "VITE_API_BASE" .env.example; then
        echo "✓ 环境变量配置正确"
    else
        echo "✗ 缺少 VITE_API_BASE 配置"
    fi
else
    echo "⚠ .env.example 文件不存在（可选）"
fi

echo ""
echo "=== 验证完成 ==="
echo "项目结构完整，可以开始开发。"
echo ""
echo "下一步："
echo "1. 运行 'npm install' 安装依赖"
echo "2. 运行 'npm run dev' 启动开发服务器"
echo "3. 访问 http://localhost:5173"