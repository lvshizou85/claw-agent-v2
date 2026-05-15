# Claw Agent v2 UI前端测试指南

## 测试框架配置

本项目使用以下测试技术栈：

### 核心依赖
- **Vitest**: 测试运行器（Vite内置）
- **@testing-library/react**: React组件测试库
- **@testing-library/jest-dom**: DOM断言扩展
- **jsdom**: 浏览器环境模拟
- **@testing-library/user-event**: 用户交互模拟

### 配置文件
- `vitest.config.ts`: Vitest配置文件
- `src/test/setup.ts`: 测试环境设置文件

## 测试文件结构

```
src/
├── components/
│   ├── __tests__/
│   │   ├── ChatWindow.test.tsx      # ChatWindow组件测试
│   │   ├── MessageBubble.test.tsx   # MessageBubble组件测试
│   │   ├── InputBox.test.tsx        # InputBox组件测试
│   │   └── integration.test.tsx     # 集成测试
│   ├── ChatWindow.tsx
│   ├── MessageBubble.tsx
│   └── InputBox.tsx
├── hooks/
│   ├── __tests__/
│   │   └── useChat.test.ts          # useChat hook测试
│   └── useChat.ts
└── test/
    └── setup.ts                     # 测试环境设置
```

## 测试用例设计

### 1. 组件测试 (Component Tests)

#### ChatWindow 组件
- 空状态渲染测试
- 消息列表显示测试
- 多种消息类型处理测试
- 滚动行为测试

#### MessageBubble 组件
- 用户/助手消息样式区分测试
- 工具调用/结果消息特殊渲染测试
- 对齐逻辑测试
- 长文本处理测试

#### InputBox 组件
- 输入处理测试
- 发送逻辑测试
- 键盘快捷键测试
- 字符计数测试
- 禁用状态测试
- 环境变量显示测试

### 2. Hook测试 (Hook Tests)

#### useChat Hook
- SSE连接测试
- API调用参数验证
- 消息流解析测试
- 错误处理机制测试
- 状态管理测试

### 3. 集成测试 (Integration Tests)
- App组件渲染测试
- 用户交互流程测试
- 环境变量读取测试
- API集成模拟测试
- 错误边界测试

## 运行测试

### 快速运行
```bash
# 运行所有测试
./run-tests.sh

# 或使用npm脚本
npm test
```

### 特定测试
```bash
# 运行组件测试
npx vitest run src/components/__tests__/

# 运行Hook测试
npx vitest run src/hooks/__tests__/

# 运行单个测试文件
npx vitest run src/components/__tests__/ChatWindow.test.tsx
```

### 带UI的运行
```bash
# 打开测试UI界面
npm run test:ui
```

### 覆盖率报告
```bash
# 生成覆盖率报告
npm run test:coverage
```

## 测试覆盖率目标

| 组件 | 行覆盖率 | 分支覆盖率 | 函数覆盖率 |
|------|----------|------------|------------|
| ChatWindow | ≥90% | ≥85% | ≥90% |
| MessageBubble | ≥95% | ≥90% | ≥95% |
| InputBox | ≥90% | ≥85% | ≥90% |
| useChat | ≥85% | ≥80% | ≥85% |

## Mock策略

### API调用Mock
```typescript
// 示例：Mock fetch API
global.fetch = vi.fn(() => 
  Promise.resolve({
    ok: true,
    status: 200,
    body: { getReader: vi.fn() }
  })
);
```

### 环境变量Mock
```typescript
// 示例：Mock环境变量
const originalEnv = import.meta.env;
import.meta.env = { ...originalEnv, VITE_API_BASE: 'http://test-api:3000' };
```

### 组件依赖Mock
```typescript
// 示例：Mock useChat hook
vi.mock('../../hooks/useChat', () => ({
  useChat: vi.fn(() => ({
    sendMessage: mockSendMessage,
    isConnecting: false,
  })),
}));
```

## 测试最佳实践

### 1. 测试命名规范
- 描述性测试名称
- 使用`should`开头
- 包含预期行为描述

### 2. 测试结构
```typescript
describe('组件名称', () => {
  beforeEach(() => {
    // 测试前设置
  });

  it('应该执行某个行为', () => {
    // 测试逻辑
  });

  afterEach(() => {
    // 测试后清理
  });
});
```

### 3. 断言使用
- 优先使用`@testing-library`的查询方法
- 使用明确的断言消息
- 验证DOM状态和组件行为

## 常见问题解决

### 1. 测试环境配置问题
```bash
# 重新安装依赖
npm install

# 清除缓存
npx vitest --clearCache
```

### 2. TypeScript类型错误
确保所有测试文件使用正确的类型导入和断言。

### 3. 异步测试超时
适当增加测试超时时间，或优化异步操作。

## 持续集成

建议在CI/CD流水线中加入以下测试步骤：

```yaml
test:
  stage: test
  script:
    - npm install
    - npm test
    - npm run test:coverage
  artifacts:
    paths:
      - coverage/
```

## 测试报告

详细测试报告请查看飞书云文档：
https://www.feishu.cn/docx/K5eEdpb5qouGSyxin5lcS4Xrnwe

报告包含：
- 测试执行概要与核心发现
- 组件测试详细分析
- SSE连接与功能测试
- 集成测试与环境配置
- 测试架构与技术栈
- 测试覆盖率与质量评估
- 问题发现与改进建议