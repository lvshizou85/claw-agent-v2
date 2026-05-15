import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import MessageBubble from '../MessageBubble'

describe('MessageBubble Component', () => {
  it('should render user message with correct styling', () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'Hello from user',
    }
    
    render(<MessageBubble message={message} />)
    
    expect(screen.getByText('Hello from user')).toBeInTheDocument()
    expect(screen.getByText('👤')).toBeInTheDocument()
    expect(screen.getByText('用户')).toBeInTheDocument()
  })

  it('should render assistant text message with correct styling', () => {
    const message = {
      id: '1',
      role: 'assistant' as const,
      content: 'Hello from assistant',
    }
    
    render(<MessageBubble message={message} />)
    
    expect(screen.getByText('Hello from assistant')).toBeInTheDocument()
    expect(screen.getByText('🤖')).toBeInTheDocument()
    expect(screen.getByText('助手')).toBeInTheDocument()
  })

  it('should render tool call message with correct styling', () => {
    const message = {
      id: '1',
      role: 'assistant' as const,
      content: '{"tool": "search", "query": "test"}',
      type: 'tool_call' as const,
    }
    
    render(<MessageBubble message={message} />)
    
    const content = screen.getByText('{"tool": "search", "query": "test"}')
    expect(content).toBeInTheDocument()
    expect(screen.getByText('🔧')).toBeInTheDocument()
    expect(screen.getByText('工具调用')).toBeInTheDocument()
    expect(content.tagName).toBe('PRE')
  })

  it('should render tool result message with correct styling', () => {
    const message = {
      id: '1',
      role: 'assistant' as const,
      content: 'Search results: test data',
      type: 'tool_result' as const,
    }
    
    render(<MessageBubble message={message} />)
    
    const content = screen.getByText('Search results: test data')
    expect(content).toBeInTheDocument()
    expect(screen.getByText('📋')).toBeInTheDocument()
    expect(screen.getByText('工具结果')).toBeInTheDocument()
    expect(content.tagName).toBe('PRE')
  })

  it('should apply correct alignment for user messages', () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'User message',
    }
    
    const { container } = render(<MessageBubble message={message} />)
    
    const bubbleWrapper = container.firstChild as HTMLElement
    expect(bubbleWrapper).toHaveClass('justify-end')
  })

  it('should apply correct alignment for assistant messages', () => {
    const message = {
      id: '1',
      role: 'assistant' as const,
      content: 'Assistant message',
    }
    
    const { container } = render(<MessageBubble message={message} />)
    
    const bubbleWrapper = container.firstChild as HTMLElement
    expect(bubbleWrapper).toHaveClass('justify-start')
  })

  it('should handle empty content gracefully', () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: '',
    }
    
    render(<MessageBubble message={message} />)
    
    expect(screen.getByText('👤')).toBeInTheDocument()
    expect(screen.getByText('用户')).toBeInTheDocument()
  })

  it('should handle long content with proper wrapping', () => {
    const longContent = 'A'.repeat(1000)
    const message = {
      id: '1',
      role: 'assistant' as const,
      content: longContent,
    }
    
    render(<MessageBubble message={message} />)
    
    expect(screen.getByText(longContent)).toBeInTheDocument()
  })
})