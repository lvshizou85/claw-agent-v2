import { useEffect, useRef } from 'react'
import MessageBubble from './MessageBubble'

interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: 'text' | 'tool_call' | 'tool_result'
}

interface ChatWindowProps {
  messages: ChatMessage[]
}

export default function ChatWindow({ messages }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="h-full flex flex-col items-center justify-center text-gray-400">
          <div className="text-center">
            <h3 className="text-xl font-medium mb-2">欢迎使用 Claw Agent v2</h3>
            <p className="text-sm">开始对话，体验多 Agent 协作能力</p>
            <p className="text-xs mt-2 text-gray-400">支持文本、工具调用、工具结果等多种消息类型</p>
          </div>
        </div>
      ) : (
        messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))
      )}
      <div ref={messagesEndRef} />
    </div>
  )
}