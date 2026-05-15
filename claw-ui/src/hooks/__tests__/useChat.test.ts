import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useChat } from '../useChat'

describe('useChat Hook', () => {
  let mockFetch: any
  let mockResponse: any
  let mockReader: any

  beforeEach(() => {
    mockReader = {
      read: vi.fn(),
      cancel: vi.fn(),
    }

    mockResponse = {
      ok: true,
      status: 200,
      statusText: 'OK',
      body: {
        getReader: vi.fn(() => mockReader),
      },
      headers: new Map(),
    }

    mockFetch = vi.fn(() => Promise.resolve(mockResponse))
    global.fetch = mockFetch
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should initialize with correct default state', () => {
    const { result } = renderHook(() => useChat())
    
    expect(result.current.isConnecting).toBe(false)
    expect(typeof result.current.sendMessage).toBe('function')
  })

  it('should set isConnecting to true when sending message', async () => {
    mockReader.read.mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat())
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    // isConnecting should be false after completion
    expect(result.current.isConnecting).toBe(false)
  })

  it('should make correct API call with default endpoint', async () => {
    mockReader.read.mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat())
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/chat/stream',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify({
          prompt: 'test prompt',
          session_context: {},
        }),
      })
    )
  })

  it('should use custom API endpoint from env variable', async () => {
    mockReader.read.mockResolvedValueOnce({ done: true, value: undefined })
    
    // Mock environment variable
    const originalEnv = import.meta.env
    import.meta.env = { ...originalEnv, VITE_API_BASE: 'http://custom-api:9000' }
    
    const { result } = renderHook(() => useChat())
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(mockFetch).toHaveBeenCalledWith(
      'http://custom-api:9000/api/chat/stream',
      expect.anything()
    )
    
    // Restore original env
    import.meta.env = originalEnv
  })

  it('should handle text messages correctly', async () => {
    const onMessage = vi.fn()
    const textData = 'data: {"type":"text","content":"Hello world"}'
    
    mockReader.read
      .mockResolvedValueOnce({ 
        done: false, 
        value: new TextEncoder().encode(textData + '\n') 
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat({ onMessage }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onMessage).toHaveBeenCalledWith({
      type: 'text',
      content: 'Hello world',
    })
  })

  it('should handle tool call messages correctly', async () => {
    const onMessage = vi.fn()
    const toolCallData = 'data: {"type":"tool_call","tool_name":"search","content":"test query"}'
    
    mockReader.read
      .mockResolvedValueOnce({ 
        done: false, 
        value: new TextEncoder().encode(toolCallData + '\n') 
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat({ onMessage }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onMessage).toHaveBeenCalledWith({
      type: 'tool_call',
      tool_name: 'search',
      content: 'test query',
    })
  })

  it('should handle tool result messages correctly', async () => {
    const onMessage = vi.fn()
    const toolResultData = 'data: {"type":"tool_result","result":"search results","content":"processed"}'
    
    mockReader.read
      .mockResolvedValueOnce({ 
        done: false, 
        value: new TextEncoder().encode(toolResultData + '\n') 
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat({ onMessage }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onMessage).toHaveBeenCalledWith({
      type: 'tool_result',
      result: 'search results',
      content: 'processed',
    })
  })

  it('should handle error messages', async () => {
    const onError = vi.fn()
    const errorData = 'data: {"type":"error","message":"Something went wrong"}'
    
    mockReader.read
      .mockResolvedValueOnce({ 
        done: false, 
        value: new TextEncoder().encode(errorData + '\n') 
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat({ onError }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onError).toHaveBeenCalledWith(new Error('Something went wrong'))
  })

  it('should call onDone when stream completes', async () => {
    const onDone = vi.fn()
    const doneData = 'data: {"type":"done"}'
    
    mockReader.read
      .mockResolvedValueOnce({ 
        done: false, 
        value: new TextEncoder().encode(doneData + '\n') 
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat({ onDone }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onDone).toHaveBeenCalledTimes(2) // Once from done event, once from stream end
  })

  it('should handle HTTP errors', async () => {
    const onError = vi.fn()
    mockResponse.ok = false
    mockResponse.status = 500
    mockResponse.statusText = 'Internal Server Error'
    
    const { result } = renderHook(() => useChat({ onError }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onError).toHaveBeenCalledWith(new Error('HTTP 500: Internal Server Error'))
  })

  it('should handle network errors', async () => {
    const onError = vi.fn()
    mockFetch.mockRejectedValueOnce(new Error('Network error'))
    
    const { result } = renderHook(() => useChat({ onError }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onError).toHaveBeenCalledWith(new Error('Network error'))
  })

  it('should handle null response body', async () => {
    const onError = vi.fn()
    mockResponse.body = null
    
    const { result } = renderHook(() => useChat({ onError }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onError).toHaveBeenCalledWith(new Error('Response body is null'))
  })

  it('should handle malformed JSON in SSE data', async () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const malformedData = 'data: {invalid json'
    
    mockReader.read
      .mockResolvedValueOnce({ 
        done: false, 
        value: new TextEncoder().encode(malformedData + '\n') 
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat())
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(consoleSpy).toHaveBeenCalled()
    consoleSpy.mockRestore()
  })

  it('should handle session context parameter', async () => {
    mockReader.read.mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat())
    const sessionContext = { userId: '123', conversationId: '456' }
    
    await act(async () => {
      result.current.sendMessage('test prompt', sessionContext)
    })
    
    expect(mockFetch).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        body: JSON.stringify({
          prompt: 'test prompt',
          session_context: sessionContext,
        }),
      })
    )
  })

  it('should handle multiple SSE events in single chunk', async () => {
    const onMessage = vi.fn()
    const onDone = vi.fn()
    
    const sseData = `data: {"type":"text","content":"Message 1"}\n\ndata: {"type":"text","content":"Message 2"}\n\ndata: {"type":"done"}\n\n`
    
    mockReader.read
      .mockResolvedValueOnce({ 
        done: false, 
        value: new TextEncoder().encode(sseData) 
      })
      .mockResolvedValueOnce({ done: true, value: undefined })
    
    const { result } = renderHook(() => useChat({ onMessage, onDone }))
    
    await act(async () => {
      result.current.sendMessage('test prompt')
    })
    
    expect(onMessage).toHaveBeenCalledTimes(2)
    expect(onMessage).toHaveBeenNthCalledWith(1, {
      type: 'text',
      content: 'Message 1',
    })
    expect(onMessage).toHaveBeenNthCalledWith(2, {
      type: 'text',
      content: 'Message 2',
    })
    expect(onDone).toHaveBeenCalled()
  })
})