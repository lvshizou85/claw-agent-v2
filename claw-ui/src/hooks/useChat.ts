import { useState, useCallback } from 'react'

interface ChatMessage {
  type: 'text' | 'tool_call' | 'tool_result' | 'error' | 'done'
  content?: string
  tool_name?: string
  result?: any
  message?: string
}

interface UseChatOptions {
  onMessage?: (message: ChatMessage) => void
  onError?: (error: Error) => void
  onDone?: () => void
}

export function useChat(options: UseChatOptions = {}) {
  const [isConnecting, setIsConnecting] = useState(false)

  const sendMessage = useCallback(async (prompt: string, sessionContext?: any) => {
    setIsConnecting(true)

    try {
      const apiBase = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
      const response = await fetch(`${apiBase}/api/chat/stream`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream'
        },
        body: JSON.stringify({ 
          prompt,
          session_context: sessionContext || {}
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      if (!response.body) {
        throw new Error('Response body is null')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          options.onDone?.()
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6).trim()
            if (!data) continue

            try {
              const parsed = JSON.parse(data) as ChatMessage
              
              if (parsed.type === 'error') {
                options.onError?.(new Error(parsed.message || 'Unknown error'))
              } else if (parsed.type === 'done') {
                options.onDone?.()
              } else {
                options.onMessage?.(parsed)
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', data, e)
            }
          }
        }
      }
    } catch (error) {
      console.error('SSE connection error:', error)
      options.onError?.(error instanceof Error ? error : new Error(String(error)))
    } finally {
      setIsConnecting(false)
    }
  }, [options])

  return {
    sendMessage,
    isConnecting
  }
}