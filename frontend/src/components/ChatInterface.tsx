import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, ChevronDown, ChevronUp, Search, FileText, PenTool, Terminal } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import type { Message, ToolActivity } from '../App'

type Props = {
  messages: Message[]
  onSendMessage: (content: string) => void
  isLoading?: boolean
}

export function ChatInterface({ messages, onSendMessage, isLoading = false }: Props) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim())
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(message => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isLoading && (
          <div className="flex items-start gap-3 animate-fade-in">
            <div className="w-8 h-8 rounded-full bg-accent-green flex items-center justify-center text-white text-sm font-medium">
              AI
            </div>
            <div className="bg-dark-surface rounded-lg px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Area */}
      <div className="border-t border-dark-border p-4">
        <form onSubmit={handleSubmit} className="flex items-end gap-3">
          <button
            type="button"
            className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
            title="Attach file"
          >
            <Paperclip className="w-5 h-5" />
          </button>
          
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type a message... (Shift+Enter for new line)"
              className="w-full bg-dark-surface border border-dark-border rounded-lg px-4 py-3 pr-12 
                text-white placeholder-gray-500 resize-none focus:outline-none focus:border-accent-blue
                transition-colors"
              rows={1}
              disabled={isLoading}
            />
          </div>
          
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3 bg-accent-blue text-white rounded-lg hover:bg-blue-600 
              disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
        
        <p className="text-xs text-gray-500 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const [showToolActivity, setShowToolActivity] = useState(false)
  const isUser = message.role === 'user'
  
  const getToolIcon = (type: ToolActivity['type']) => {
    switch (type) {
      case 'search': return <Search className="w-3 h-3 text-accent-blue" />
      case 'read': return <FileText className="w-3 h-3 text-accent-green" />
      case 'write': return <PenTool className="w-3 h-3 text-accent-orange" />
      case 'execute': return <Terminal className="w-3 h-3 text-accent-purple" />
    }
  }
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  return (
    <div className={`flex items-start gap-3 animate-fade-in ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium shrink-0
        ${isUser ? 'bg-accent-blue' : 'bg-accent-green'}`}
      >
        {isUser ? 'You' : 'AI'}
      </div>
      
      <div className={`flex flex-col max-w-[80%] ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`rounded-lg px-4 py-3 ${isUser ? 'bg-accent-blue text-white' : 'bg-dark-surface text-gray-200'}`}>
          {isUser ? (
            <div className="whitespace-pre-wrap">{message.content}</div>
          ) : (
            <div className="prose prose-invert prose-sm max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={{
                  table: ({node, ...props}) => (
                    <table className="border-collapse border border-gray-600 my-4" {...props} />
                  ),
                  thead: ({node, ...props}) => (
                    <thead className="bg-gray-800" {...props} />
                  ),
                  th: ({node, ...props}) => (
                    <th className="border border-gray-600 px-4 py-2 text-left" {...props} />
                  ),
                  td: ({node, ...props}) => (
                    <td className="border border-gray-600 px-4 py-2" {...props} />
                  ),
                  code: ({node, inline, ...props}: any) => (
                    inline ? 
                      <code className="bg-gray-800 px-1 py-0.5 rounded text-sm" {...props} /> :
                      <code className="block bg-gray-800 p-3 rounded my-2 overflow-x-auto" {...props} />
                  ),
                  pre: ({node, ...props}) => (
                    <pre className="bg-gray-800 p-3 rounded my-2 overflow-x-auto" {...props} />
                  ),
                  ul: ({node, ...props}) => (
                    <ul className="list-disc list-inside my-2" {...props} />
                  ),
                  ol: ({node, ...props}) => (
                    <ol className="list-decimal list-inside my-2" {...props} />
                  ),
                  blockquote: ({node, ...props}) => (
                    <blockquote className="border-l-4 border-accent-blue pl-4 italic my-2" {...props} />
                  ),
                  h1: ({node, ...props}) => (
                    <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />
                  ),
                  h2: ({node, ...props}) => (
                    <h2 className="text-xl font-bold mt-3 mb-2" {...props} />
                  ),
                  h3: ({node, ...props}) => (
                    <h3 className="text-lg font-bold mt-2 mb-1" {...props} />
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
          <span>{formatTime(message.timestamp)}</span>
          
          {message.toolActivity && message.toolActivity.length > 0 && (
            <button
              onClick={() => setShowToolActivity(!showToolActivity)}
              className="flex items-center gap-1 text-gray-400 hover:text-white transition-colors"
            >
              <span>Tool Activity ({message.toolActivity.length})</span>
              {showToolActivity ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          )}
        </div>
        
        {showToolActivity && message.toolActivity && (
          <div className="mt-2 bg-gray-900/50 backdrop-blur rounded-lg border border-gray-700 overflow-hidden w-full">
            <div className="px-3 py-2 bg-gray-800/50 border-b border-gray-700">
              <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
                Tool Activity Log
              </span>
            </div>
            <div className="p-3 space-y-2">
              {message.toolActivity.map((activity, idx) => (
                <div 
                  key={idx} 
                  className="flex items-start gap-3 p-2 rounded-md hover:bg-gray-800/50 transition-colors"
                >
                  <div className="mt-0.5 shrink-0">
                    {getToolIcon(activity.type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-200 break-words">{activity.description}</div>
                    {activity.filePath && (
                      <div className="text-xs text-gray-500 mt-1">
                        <FileText className="w-3 h-3 inline mr-1" />
                        {activity.filePath}
                      </div>
                    )}
                  </div>
                  <span className="text-xs text-gray-500 whitespace-nowrap">
                    {formatTime(activity.timestamp)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
