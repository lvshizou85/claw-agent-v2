export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'tool_call' | 'tool_result'
  timestamp?: number
}

export interface SSEEvent {
  type: 'text' | 'tool_call' | 'tool_result' | 'error' | 'done'
  content?: string
  tool_name?: string
  result?: any
  message?: string
}

export interface ChatRequest {
  prompt: string
  session_context?: Record<string, any>
}

export interface ChatResponse {
  success: boolean
  message?: string
  data?: any
}