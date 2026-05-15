interface MessageBubbleProps {
  message: {
    id: string
    role: 'user' | 'assistant'
    content: string
    type?: 'text' | 'tool_call' | 'tool_result'
  }
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user'
  const isToolCall = message.type === 'tool_call'
  const isToolResult = message.type === 'tool_result'

  const getBubbleStyle = () => {
    if (isUser) {
      return 'bg-blue-500 text-white rounded-br-none'
    }
    if (isToolCall) {
      return 'bg-yellow-100 text-yellow-800 border border-yellow-200'
    }
    if (isToolResult) {
      return 'bg-green-50 text-green-800 border border-green-200'
    }
    return 'bg-gray-100 text-gray-800 rounded-bl-none'
  }

  const getIcon = () => {
    if (isUser) return '👤'
    if (isToolCall) return '🔧'
    if (isToolResult) return '📋'
    return '🤖'
  }

  const getRoleText = () => {
    if (isUser) return '用户'
    if (isToolCall) return '工具调用'
    if (isToolResult) return '工具结果'
    return '助手'
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[80%] ${isUser ? 'ml-auto' : 'mr-auto'}`}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-sm">{getIcon()}</span>
          <span className={`text-xs font-medium ${
            isUser ? 'text-blue-600' : 
            isToolCall ? 'text-yellow-600' : 
            isToolResult ? 'text-green-600' : 'text-gray-600'
          }`}>
            {getRoleText()}
          </span>
        </div>
        <div className={`px-4 py-3 rounded-2xl ${getBubbleStyle()}`}>
          {isToolCall || isToolResult ? (
            <pre className="whitespace-pre-wrap font-mono text-sm overflow-x-auto">
              {message.content}
            </pre>
          ) : (
            <p className="whitespace-pre-wrap">{message.content}</p>
          )}
        </div>
      </div>
    </div>
  )
}