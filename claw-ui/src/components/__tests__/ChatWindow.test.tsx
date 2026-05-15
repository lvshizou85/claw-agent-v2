import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import ChatWindow from '../ChatWindow'

describe('ChatWindow Component', () => {
  it('should render empty state when no messages', () => {
    render(<ChatWindow messages={[]} />)
    
    expect(screen.getByText('欢迎使用 Claw Agent v2')).toBeInTheDocument()
    expect(screen.getByText('开始对话，体验多 Agent 协作能力')).toBeInTheDocument()
    expect(screen.getByText('支持文本、工具调用、工具结果等多种消息类型')).toBeInTheDocument()
  })

  it('should render user messages', () => {
    const messages = [
      { id: '1', role: 'user', content: 'Hello, world!' as string },
    ]
    
    render(<ChatWindow messages={messages} />)
    
    expect(screen.getByText('Hello, world!')).toBeInTheDocument()
  })

  it('should render assistant messages', () => {
    const messages = [
      { id: '1', role: 'assistant', content: 'How can I help you?' as string },
    ]
    
    render(<ChatWindow messages={messages} />)
    
    expect(screen.getByText('How can I help you?')).toBeInTheDocument()
  })

  it('should render tool call messages', () => {
    const messages = [
      { 
        id: '1', 
        role: 'assistant', 
        content: '{"tool": "search", "query": "test"}' as string,
        type: 'tool_call' as const
      },
    ]
    
    render(<ChatWindow messages={messages} />)
    
    expect(screen.getByText('{"tool": "search", "query": "test"}')).toBeInTheDocument()
  })

  it('should render tool result messages', () => {
    const messages = [
      { 
        id: '1', 
        role: 'assistant', 
        content: 'Search results: test data' as string,
        type: 'tool_result' as const
      },
    ]
    
    render(<ChatWindow messages={messages} />)
    
    expect(screen.getByText('Search results: test data')).toBeInTheDocument()
  })

  it('should render multiple messages in correct order', () => {
    const messages = [
      { id: '1', role: 'user', content: 'Hello' as string },
      { id: '2', role: 'assistant', content: 'Hi there!' as string },
      { 
        id: '3', 
        role: 'assistant', 
        content: '{"action": "search"}' as string,
        type: 'tool_call' as const
      },
    ]
    
    render(<ChatWindow messages={messages} />)
    
    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
    expect(screen.getByText('{"action": "search"}')).toBeInTheDocument()
  })
})