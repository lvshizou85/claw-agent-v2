import { useState } from 'react'
import ChatWindow from './components/ChatWindow'
import InputBox from './components/InputBox'
import { useChat } from './hooks/useChat'

export default function App() {
  const [messages, setMessages] = useState<Array<{
    id: string
    role: 'user' | 'assistant'
    content: string
    type?: 'text' | 'tool_call' | 'tool_result'
  }>>([])

  const { sendMessage, isConnecting } = useChat({
    onMessage: (msg) => {
      if (msg.type === 'text') {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.role === 'assistant' && last?.type === 'text') {
            return [...prev.slice(0, -1), { ...last, content: last.content + msg.content }]
          }
          return [...prev, {
            id: Date.now().toString(),
            role: 'assistant',
            content: msg.content,
            type: 'text'
          }]
        })
      } else if (msg.type === 'tool_call') {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: `调用工具: ${msg.tool_name}`,
          type: 'tool_call'
        }])
      } else if (msg.type === 'tool_result') {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: `工具结果: ${JSON.stringify(msg.result, null, 2)}`,
          type: 'tool_result'
        }])
      }
    },
    onError: (error) => {
      console.error('SSE连接错误:', error)
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `连接错误: ${error.message}`
      }])
    }
  })

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || isConnecting) return

    const userMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      content: content.trim()
    }
    setMessages(prev => [...prev, userMessage])

    await sendMessage(content.trim())
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* 头部 */}
      <header className="bg-white border-b px-6 py-4">
        <h1 className="text-2xl font-bold text-gray-800">Claw Agent v2</h1>
        <p className="text-sm text-gray-500 mt-1">基于 Claude Runtime 的多 Agent 协作平台</p>
      </header>

      {/* 聊天窗口 */}
      <main className="flex-1 overflow-hidden">
        <ChatWindow messages={messages} />
      </main>

      {/* 输入区域 */}
      <footer className="bg-white border-t p-4">
        <InputBox 
          onSendMessage={handleSendMessage}
          isSending={isConnecting}
        />
      </footer>
    </div>
  )
}