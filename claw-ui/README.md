# Claw UI - Claw Agent v2 前端界面

基于 React + Vite + Tailwind 构建的 Claw Agent v2 前端界面，支持 SSE 流式对话和工具调用。

## 功能特性

- **SSE 流式对话**: 支持实时流式消息传输
- **多消息类型**: 支持文本、工具调用、工具结果等多种消息类型
- **响应式设计**: 适配不同屏幕尺寸
- **现代化界面**: 使用 Tailwind CSS 构建的现代化 UI
- **TypeScript 支持**: 完整的类型安全

## 项目结构

```
claw-ui/
├── src/
│   ├── components/          # React 组件
│   │   ├── ChatWindow.tsx   # 聊天窗口组件
│   │   ├── MessageBubble.tsx # 消息气泡组件
│   │   └── InputBox.tsx     # 输入框组件
│   ├── hooks/
│   │   └── useChat.ts       # SSE 连接 Hook
│   ├── types/
│   │   └── index.ts         # 类型定义
│   ├── App.tsx              # 主应用组件
│   ├── main.tsx             # 应用入口
│   └── index.css            # 全局样式
├── index.html               # HTML 入口
├── vite.config.ts           # Vite 配置
├── tailwind.config.js       # Tailwind 配置
├── tsconfig.json            # TypeScript 配置
├── nginx.conf               # Nginx 配置（生产环境）
└── package.json             # 依赖管理
```

## 快速开始

### 1. 安装依赖

```bash
cd /home/gem/.aily/workspace/claw-agent-v2/claw-ui
npm install
```

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置 API 基础地址：

```env
VITE_API_BASE=http://localhost:8000
```

### 3. 启动开发服务器

```bash
npm run dev
```

开发服务器将在 `http://localhost:5173` 启动。

### 4. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

## 开发指南

### API 集成

前端通过 SSE (Server-Sent Events) 与后端通信：

```typescript
// 发送消息示例
const response = await fetch(`${apiBase}/api/chat/stream`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ 
    prompt: "Hello", 
    session_context: {} 
  }),
});
```

### 消息类型

支持的消息类型：

1. **text**: 文本消息
2. **tool_call**: 工具调用消息
3. **tool_result**: 工具执行结果

### 样式开发

项目使用 Tailwind CSS，可以通过修改 `tailwind.config.js` 自定义主题：

```javascript
export default {
  theme: {
    extend: {
      colors: {
        claw: {
          primary: '#4F46E5',
          secondary: '#10B981',
        }
      }
    }
  }
}
```

## 部署

### Docker 部署

项目包含 Docker 支持，可以使用以下命令构建和运行：

```bash
# 构建镜像
docker build -t claw-ui .

# 运行容器
docker run -p 80:80 claw-ui
```

### Nginx 配置

生产环境使用 `nginx.conf` 配置文件，支持：

- SPA 路由
- API 代理
- 静态资源缓存
- Gzip 压缩

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| VITE_API_BASE | API 基础地址 | http://localhost:8000 |

## 技术栈

- **React 18**: UI 框架
- **TypeScript**: 类型安全
- **Vite**: 构建工具
- **Tailwind CSS**: 样式框架
- **React Router**: 路由管理
- **SSE**: 服务器发送事件

## 许可证

本项目遵循 Claw Agent v2 项目的许可证。