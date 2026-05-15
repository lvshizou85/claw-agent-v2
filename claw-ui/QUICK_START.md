# Claw UI 快速启动指南

## 环境要求

- Node.js 18+
- npm 或 yarn

## 安装步骤

### 1. 进入项目目录

```bash
cd /home/gem/.aily/workspace/claw-agent-v2/claw-ui
```

### 2. 安装依赖

```bash
npm install
```

### 3. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置 API 地址：

```env
VITE_API_BASE=http://localhost:8000
```

### 4. 启动开发服务器

```bash
npm run dev
```

### 5. 访问应用

打开浏览器访问：http://localhost:5173

## 项目结构说明

```
claw-ui/
├── src/
│   ├── components/          # React 组件
│   │   ├── ChatWindow.tsx   # 聊天窗口组件
│   │   ├── MessageBubble.tsx # 消息气泡组件
│   │   └── InputBox.tsx     # 输入框组件
│   ├── hooks/
│   │   └── useChat.ts       # SSE 连接 Hook
│   ├── App.tsx              # 主应用组件
│   └── main.tsx             # 应用入口
├── package.json             # 依赖配置
├── vite.config.ts           # 构建配置
└── tailwind.config.js       # 样式配置
```

## 核心功能

### 1. SSE 流式对话

前端通过 `useChat` Hook 连接到 `/api/chat/stream` 端点，支持实时消息流。

### 2. 多消息类型支持

- **文本消息**: 普通对话消息
- **工具调用消息**: 显示调用的工具名称
- **工具结果消息**: 显示工具执行结果

### 3. 响应式 UI

使用 Tailwind CSS 构建的现代化响应式界面。

## 开发命令

```bash
# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览构建结果
npm run preview

# 代码检查
npm run lint
```

## 与后端集成

确保后端服务（claw-gateway）在 `http://localhost:8000` 运行，支持以下端点：

- `POST /api/chat/stream` - SSE 流式对话接口

## 故障排除

### 1. 依赖安装失败

```bash
# 清除 npm 缓存
npm cache clean --force

# 重新安装
rm -rf node_modules package-lock.json
npm install
```

### 2. 开发服务器无法启动

检查端口占用：

```bash
# 查看端口占用
lsof -i :5173

# 如果端口被占用，可以在 vite.config.ts 中修改端口
```

### 3. API 连接失败

检查 `.env` 文件中的 `VITE_API_BASE` 配置是否正确，确保后端服务正在运行。

## 生产部署

### Docker 部署

```bash
# 构建 Docker 镜像
docker build -t claw-ui .

# 运行容器
docker run -p 80:80 claw-ui
```

### 手动部署

```bash
# 构建项目
npm run build

# 构建产物在 dist/ 目录
# 可以使用任何静态文件服务器部署
```

## 技术支持

如有问题，请参考：
- [项目 README](./README.md)
- [Vite 文档](https://vitejs.dev/)
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [React 文档](https://react.dev/)