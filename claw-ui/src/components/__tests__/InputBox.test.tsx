import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import InputBox from '../InputBox'

describe('InputBox Component', () => {
  it('should render input box with placeholder', () => {
    const mockSendMessage = vi.fn()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    expect(screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')).toBeInTheDocument()
    expect(screen.getByText('发送')).toBeInTheDocument()
  })

  it('should update input value when typing', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    await user.type(textarea, 'Hello, world!')
    
    expect(textarea).toHaveValue('Hello, world!')
  })

  it('should call onSendMessage when form is submitted', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    await user.type(textarea, 'Test message')
    
    const submitButton = screen.getByText('发送')
    await user.click(submitButton)
    
    expect(mockSendMessage).toHaveBeenCalledWith('Test message')
  })

  it('should clear input after sending message', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    await user.type(textarea, 'Test message')
    
    const submitButton = screen.getByText('发送')
    await user.click(submitButton)
    
    expect(textarea).toHaveValue('')
  })

  it('should not send empty message', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    const submitButton = screen.getByText('发送')
    await user.click(submitButton)
    
    expect(mockSendMessage).not.toHaveBeenCalled()
  })

  it('should not send message when isSending is true', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={true} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    await user.type(textarea, 'Test message')
    
    const submitButton = screen.getByText('发送中')
    expect(submitButton).toBeDisabled()
    
    await user.click(submitButton)
    expect(mockSendMessage).not.toHaveBeenCalled()
  })

  it('should send message on Enter key press', async () => {
    const mockSendMessage = vi.fn()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' })
    
    expect(mockSendMessage).toHaveBeenCalledWith('Test message')
  })

  it('should not send message on Shift+Enter (should add newline)', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    await user.type(textarea, 'Line 1')
    await user.keyboard('{Shift>}{Enter}{/Shift}')
    await user.type(textarea, 'Line 2')
    
    expect(textarea).toHaveValue('Line 1\nLine 2')
    expect(mockSendMessage).not.toHaveBeenCalled()
  })

  it('should show character count', async () => {
    const mockSendMessage = vi.fn()
    const user = userEvent.setup()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    await user.type(textarea, 'Hello')
    
    expect(screen.getByText('5/5000')).toBeInTheDocument()
  })

  it('should show API endpoint from environment variable', () => {
    const mockSendMessage = vi.fn()
    
    // Mock environment variable
    const originalEnv = import.meta.env
    import.meta.env = { ...originalEnv, VITE_API_BASE: 'http://test-api:3000' }
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    expect(screen.getByText('连接地址: http://test-api:3000/api/chat/stream')).toBeInTheDocument()
    
    // Restore original env
    import.meta.env = originalEnv
  })

  it('should show default API endpoint when env var is not set', () => {
    const mockSendMessage = vi.fn()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    expect(screen.getByText('连接地址: http://localhost:8000/api/chat/stream')).toBeInTheDocument()
  })

  it('should disable input when isSending is true', () => {
    const mockSendMessage = vi.fn()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={true} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    expect(textarea).toBeDisabled()
  })

  it('should enable input when isSending is false', () => {
    const mockSendMessage = vi.fn()
    
    render(<InputBox onSendMessage={mockSendMessage} isSending={false} />)
    
    const textarea = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    expect(textarea).not.toBeDisabled()
  })
})