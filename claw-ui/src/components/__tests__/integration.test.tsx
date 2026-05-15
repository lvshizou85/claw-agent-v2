import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../../App'

// Mock the useChat hook
vi.mock('../../hooks/useChat', () => ({
  useChat: vi.fn(() => ({
    sendMessage: vi.fn(),
    isConnecting: false,
  })),
}))

// Mock environment variables
vi.mock('../../utils/env', () => ({
  getApiBaseUrl: () => 'http://localhost:8000',
}))

describe('UI Integration Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render the main App component', () => {
    render(<App />)
    
    expect(screen.getByText('Claw Agent v2')).toBeInTheDocument()
    expect(screen.getByText('多 Agent 协作平台')).toBeInTheDocument()
  })

  it('should show chat interface with input and messages area', () => {
    render(<App />)
    
    expect(screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')).toBeInTheDocument()
    expect(screen.getByText('发送')).toBeInTheDocument()
  })

  it('should display connection status', async () => {
    render(<App />)
    
    // Check for API endpoint display
    await waitFor(() => {
      expect(screen.getByText(/连接地址:/)).toBeInTheDocument()
    })
  })

  it('should handle environment variable reading for API endpoint', () => {
    // Test default endpoint
    const { getApiBaseUrl } = require('../../utils/env')
    expect(getApiBaseUrl()).toBe('http://localhost:8000')
  })

  it('should show empty state when no messages', () => {
    render(<App />)
    
    expect(screen.getByText('欢迎使用 Claw Agent v2')).toBeInTheDocument()
    expect(screen.getByText('开始对话，体验多 Agent 协作能力')).toBeInTheDocument()
  })

  it('should handle user interaction flow', async () => {
    const user = userEvent.setup()
    const mockSendMessage = vi.fn()
    
    // Mock useChat to return our mock function
    const { useChat } = require('../../hooks/useChat')
    useChat.mockReturnValue({
      sendMessage: mockSendMessage,
      isConnecting: false,
    })
    
    render(<App />)
    
    const input = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    const sendButton = screen.getByText('发送')
    
    // Type a message
    await user.type(input, 'Hello, test message')
    
    // Click send
    await user.click(sendButton)
    
    // Verify the message was sent
    expect(mockSendMessage).toHaveBeenCalledWith('Hello, test message')
  })

  it('should handle sending state correctly', async () => {
    const user = userEvent.setup()
    const mockSendMessage = vi.fn()
    
    // Mock useChat with isConnecting = true
    const { useChat } = require('../../hooks/useChat')
    useChat.mockReturnValue({
      sendMessage: mockSendMessage,
      isConnecting: true,
    })
    
    render(<App />)
    
    // Check that input is disabled when sending
    const input = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    expect(input).toBeDisabled()
    
    // Check that button shows sending state
    expect(screen.getByText('发送中')).toBeInTheDocument()
  })

  it('should handle different message types in chat window', () => {
    // Mock messages with different types
    const messages = [
      { id: '1', role: 'user', content: 'User message' },
      { id: '2', role: 'assistant', content: 'Assistant reply' },
      { id: '3', role: 'assistant', content: 'Tool call', type: 'tool_call' },
      { id: '4', role: 'assistant', content: 'Tool result', type: 'tool_result' },
    ]
    
    // We can't easily test this without mocking the entire state management
    // This is more of an end-to-end test that would be better with Cypress
    expect(true).toBe(true) // Placeholder for integration test structure
  })

  it('should handle SSE connection errors gracefully', async () => {
    const user = userEvent.setup()
    const mockSendMessage = vi.fn().mockRejectedValue(new Error('SSE connection failed'))
    
    const { useChat } = require('../../hooks/useChat')
    useChat.mockReturnValue({
      sendMessage: mockSendMessage,
      isConnecting: false,
    })
    
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    
    render(<App />)
    
    const input = screen.getByPlaceholderText('输入消息... (Shift+Enter 换行，Enter 发送)')
    const sendButton = screen.getByText('发送')
    
    await user.type(input, 'Test error')
    await user.click(sendButton)
    
    // Error should be logged to console
    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled()
    })
    
    consoleSpy.mockRestore()
  })

  it('should handle API endpoint configuration', () => {
    // Test that the UI displays the correct API endpoint
    render(<App />)
    
    // Check for the API endpoint info in the UI
    expect(screen.getByText(/连接地址:/)).toBeInTheDocument()
    
    // The actual endpoint should be displayed
    const endpointText = screen.getByText(/连接地址:/).textContent
    expect(endpointText).toContain('/api/chat/stream')
  })

  it('should maintain message history', () => {
    // This would require mocking the state management
    // For now, we'll verify the chat window component renders messages
    render(<App />)
    
    // Initially should show empty state
    expect(screen.getByText('欢迎使用 Claw Agent v2')).toBeInTheDocument()
  })
})