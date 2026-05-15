import { useState, KeyboardEvent } from 'react'

interface InputBoxProps {
  onSendMessage: (content: string) => void
  isSending: boolean
}

export default function InputBox({ onSendMessage, isSending }: InputBoxProps) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isSending) return
    onSendMessage(input)
    setInput('')
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
      <div className="flex gap-3">
        <div className="flex-1 relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息... (Shift+Enter 换行，Enter 发送)"
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={3}
            disabled={isSending}
          />
          <div className="absolute right-2 bottom-2 text-xs text-gray-400">
            {input.length}/5000
          </div>
        </div>
        <button
          type="submit"
          disabled={isSending || !input.trim()}
          className="self-end px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSending ? (
            <span className="flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              发送中
            </span>
          ) : (
            '发送'
          )}
        </button>
      </div>
      <div className="mt-2 text-xs text-gray-500">
        <p>• 支持文本对话、工具调用</p>
        <p>• 连接地址: {import.meta.env.VITE_API_BASE || 'http://localhost:8000'}/api/chat/stream</p>
      </div>
    </form>
  )
}