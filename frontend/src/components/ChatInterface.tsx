import { useState, useRef, useEffect } from 'react'
import { Send, Paperclip, ChevronDown, FileText, X } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import type { Message } from '../App'

type Props = {
  messages: Message[]
  onSendMessage: (content: string, mentionedFiles?: string[]) => void
  isLoading?: boolean
  availableFiles?: string[]
}

export function ChatInterface({ messages, onSendMessage, isLoading = false, availableFiles = [] }: Props) {
  const [input, setInput] = useState('')
  const [mentionedFiles, setMentionedFiles] = useState<string[]>([])
  const [showMentionDropdown, setShowMentionDropdown] = useState(false)
  const [mentionFilter, setMentionFilter] = useState('')
  const [mentionPosition, setMentionPosition] = useState(0)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  // Handle @ mentions
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    const cursorPos = textarea.selectionStart
    const textBeforeCursor = input.slice(0, cursorPos)
    const lastAtIndex = textBeforeCursor.lastIndexOf('@')
    
    if (lastAtIndex !== -1 && lastAtIndex === textBeforeCursor.length - 1) {
      // Just typed @
      setShowMentionDropdown(true)
      setMentionFilter('')
      setMentionPosition(lastAtIndex)
    } else if (lastAtIndex !== -1) {
      const textAfterAt = textBeforeCursor.slice(lastAtIndex + 1)
      if (!textAfterAt.includes(' ') && textAfterAt.length > 0) {
        // Typing after @
        setShowMentionDropdown(true)
        setMentionFilter(textAfterAt)
        setMentionPosition(lastAtIndex)
      } else if (textAfterAt.includes(' ')) {
        setShowMentionDropdown(false)
      }
    } else {
      setShowMentionDropdown(false)
    }
  }, [input])

  const filteredFiles = availableFiles.filter(file => 
    file.toLowerCase().includes(mentionFilter.toLowerCase())
  ).slice(0, 10)

  const handleMentionSelect = (file: string) => {
    const beforeMention = input.slice(0, mentionPosition)
    const afterMention = input.slice(textareaRef.current?.selectionStart || input.length)
    const newInput = beforeMention + `@${file} ` + afterMention
    setInput(newInput)
    setShowMentionDropdown(false)
    
    if (!mentionedFiles.includes(file)) {
      setMentionedFiles([...mentionedFiles, file])
    }
    
    textareaRef.current?.focus()
  }

  const removeMentionedFile = (file: string) => {
    setMentionedFiles(mentionedFiles.filter(f => f !== file))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim(), mentionedFiles)
      setInput('')
      setMentionedFiles([])
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="flex-1 flex flex-col h-full max-w-[900px] mx-auto w-full px-6">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden py-12 flex flex-col gap-8 min-h-0">
        {messages.map(message => (
          <MessageBubble key={message.id} message={message} />
        ))}
        
        {isLoading && (
          <div className="flex items-start gap-4 animate-slide-in">
            <div className="flex gap-1.5 pt-1">
              <span className="w-2 h-2 bg-white/40 rounded-full animate-typing" />
              <span className="w-2 h-2 bg-white/40 rounded-full animate-typing-delay-1" />
              <span className="w-2 h-2 bg-white/40 rounded-full animate-typing-delay-2" />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input Container */}
      <div className="py-6 sticky bottom-0 bg-gradient-to-t from-[#1e1e1e] via-[#1e1e1e] to-transparent">
        {/* Mentioned Files Pills */}
        {mentionedFiles.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2">
            {mentionedFiles.map(file => (
              <div
                key={file}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/10 border border-[rgba(59,130,246,0.2)] 
                  rounded-full text-sm text-blue-400 transition-all hover:bg-blue-500/15 hover:border-[rgba(59,130,246,0.3)]">

                <FileText className="w-3.5 h-3.5" />
                <span>{file}</span>
                <button
                  onClick={() => removeMentionedFile(file)}
                  className="w-3.5 h-3.5 flex items-center justify-center hover:bg-blue-500/20 rounded-full transition-colors"
                >
                  <X className="w-2.5 h-2.5" />
                </button>
              </div>
            ))}
          </div>
        )}
        
        {/* Input Wrapper */}
        <form onSubmit={handleSubmit}>
          <div className="flex items-end gap-3 bg-[rgba(255,255,255,0.04)] border-[1.5px] border-[rgba(255,255,255,0.08)] rounded-2xl p-3 
            transition-all duration-300 focus-within:bg-[rgba(255,255,255,0.06)] focus-within:border-[rgba(59,130,246,0.4)] focus-within:shadow-[0_0_0_4px_rgba(59,130,246,0.08)]">
            <button
              type="button"
              className="w-8 h-8 flex items-center justify-center text-white/50 hover:text-white/90 
                hover:bg-white/8 rounded-lg transition-all flex-shrink-0"
              title="Attach file"
            >
              <Paperclip className="w-[18px] h-[18px]" />
            </button>
            
            <div className="flex-1 relative">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message... (@ to mention files, Shift+Enter for new line)"
                className="w-full bg-transparent border-none text-white text-[15px] placeholder-white/40 
                  resize-none outline-none leading-6 max-h-[200px]"
                rows={1}
                disabled={isLoading}
              />
              
              {/* Mention Dropdown */}
              {showMentionDropdown && filteredFiles.length > 0 && (
                <div
                  ref={dropdownRef}
                  className="absolute bottom-full left-0 mb-2 w-full max-h-60 overflow-y-auto bg-[#2a2a2a] 
                    border border-[rgba(255,255,255,0.08)] rounded-xl shadow-2xl z-50">

                  {filteredFiles.map(file => (
                    <button
                      key={file}
                      type="button"
                      onClick={() => handleMentionSelect(file)}
                      className="w-full flex items-center gap-2 px-4 py-2.5 hover:bg-white/8 text-left text-sm text-white/90 
                        transition-colors"
                    >
                      <FileText className="w-4 h-4 text-blue-400" />
                      <span>{file}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
            
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="w-9 h-9 flex items-center justify-center bg-gradient-to-br from-blue-500 to-blue-600 
                text-white rounded-[10px] transition-all duration-200 hover:scale-105 hover:shadow-[0_4px_12px_rgba(59,130,246,0.3)] 
                active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100 
                disabled:hover:shadow-none flex-shrink-0"
            >
              <Send className="w-[18px] h-[18px]" />
            </button>
          </div>
          
          <p className="text-xs text-white/30 mt-2 text-center">
            Pro tip: Use @ to mention files • Shift+Enter for new line
          </p>
        </form>
      </div>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const [showToolActivity, setShowToolActivity] = useState(false)
  const [expandedTools, setExpandedTools] = useState<Set<number>>(new Set())
  const isUser = message.role === 'user'
  
  const getToolIcon = () => {
    return <div className="w-2 h-2 rounded-full bg-white/30 flex-shrink-0" />
  }
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  const toggleToolItem = (index: number) => {
    const newExpanded = new Set(expandedTools)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedTools(newExpanded)
  }

  return (
    <div className={`flex items-start gap-4 animate-slide-in ${isUser ? 'ml-auto max-w-[75%]' : 'mr-auto max-w-full'}`}>
      {/* User messages: card style, Assistant messages: transparent */}
      <div className="flex-1 pt-1">
        <div className={`${isUser 
          ? 'bg-[rgba(20,20,20,0.6)] backdrop-blur-[40px] border border-[rgba(255,255,255,0.06)] rounded-2xl px-4 py-4' 
          : 'bg-transparent'
        }`}>
          <div className={`text-[15px] leading-[1.6] tracking-[-0.1px] ${isUser ? 'text-white/90' : 'text-white/90'}`}>
            {isUser ? (
              <div className="whitespace-pre-wrap">{message.content}</div>
            ) : (
              <div className="prose prose-invert prose-sm max-w-none [&_p]:mb-3 [&_p:last-child]:mb-0">
                <ReactMarkdown
                  remarkPlugins={[remarkGfm]}
                  rehypePlugins={[rehypeHighlight]}
                  components={{
                    p: ({node, ...props}) => <p className="mb-3 last:mb-0" {...props} />,
                    code: ({node, className, children, ...props}) => {
                      const match = /language-(\w+)/.exec(className || '')
                      const isInline = !match
                      return isInline ? 
                        <code className="bg-black/40 px-1.5 py-0.5 rounded text-sm text-[#a5d6ff]" {...props}>{children}</code> :
                        <code className="block bg-black/40 border border-white/8 rounded-xl p-4 my-3 overflow-x-auto text-[13px] text-[#a5d6ff] font-mono" {...props}>{children}</code>
                    },
                    pre: ({node, ...props}) => (
                      <pre className="bg-black/40 border border-white/8 rounded-xl p-4 my-3 overflow-x-auto" {...props} />
                    ),
                    ul: ({node, ...props}) => (
                      <ul className="list-disc list-inside my-2 space-y-1" {...props} />
                    ),
                    ol: ({node, ...props}) => (
                      <ol className="list-decimal list-inside my-2 space-y-1" {...props} />
                    ),
                    h1: ({node, ...props}) => <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />,
                    h2: ({node, ...props}) => <h2 className="text-xl font-bold mt-3 mb-2" {...props} />,
                    h3: ({node, ...props}) => <h3 className="text-lg font-bold mt-2 mb-1" {...props} />,
                    strong: ({node, ...props}) => <strong className="font-semibold" {...props} />,
                  }}
                >
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </div>
        
        {/* Tool Activity Toggle - Only for assistant messages */}
        {!isUser && message.toolActivity && message.toolActivity.length > 0 && (
          <>
            <button
              onClick={() => setShowToolActivity(!showToolActivity)}
              className={`inline-flex items-center gap-2 px-3.5 py-2 mt-2 bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] rounded-[10px] 
                text-white/70 text-[13px] font-medium transition-all hover:bg-[rgba(255,255,255,0.08)] hover:border-[rgba(255,255,255,0.12)] hover:text-white/90
                ${showToolActivity ? 'bg-[rgba(255,255,255,0.08)] border-[rgba(255,255,255,0.12)]' : ''}`}>

              <span>Tools Used</span>
              <span className="inline-flex items-center justify-center min-w-[22px] h-[22px] px-1.5 
                bg-white/10 rounded-[11px] text-xs font-semibold text-white/90">
                {message.toolActivity.length}
              </span>
              <ChevronDown className={`w-4 h-4 text-white/50 transition-transform ${showToolActivity ? 'rotate-180' : ''}`} />
            </button>

            {/* Tool Panel */}
            {showToolActivity && (
              <div className="mt-3 bg-[rgba(255,255,255,0.02)] border border-[rgba(255,255,255,0.06)] rounded-xl overflow-hidden">
                <div className="px-4 py-3.5 border-b border-[rgba(255,255,255,0.06)]">
                  <div className="text-[11px] font-semibold text-white/50 uppercase tracking-[0.8px]">
                    Execution Log
                  </div>
                </div>

                <div className="p-2">
                  {message.toolActivity.map((activity, idx) => (
                    <div key={idx} className="mb-2 last:mb-0">
                      <div 
                        className="bg-transparent border border-[rgba(255,255,255,0.04)] rounded-lg overflow-hidden 
                          transition-all hover:bg-[rgba(255,255,255,0.02)] hover:border-[rgba(255,255,255,0.08)]">

                        <div 
                          className="flex items-center gap-3 px-3 py-3 cursor-pointer"
                          onClick={() => toggleToolItem(idx)}
                        >
                          {getToolIcon()}
                          
                          <div className="flex-1 min-w-0">
                            <div className="text-[13px] font-medium text-white/90 font-mono mb-0.5">
                              {activity.type}
                            </div>
                            <div className="text-[13px] text-white/50 truncate">
                              {activity.description}
                            </div>
                          </div>
                          
                          <div className="flex items-center gap-3 text-xs text-white/30">
                            <span className="font-mono">{formatTime(activity.timestamp)}</span>
                            <ChevronDown className={`w-4 h-4 text-white/30 transition-transform flex-shrink-0 
                              ${expandedTools.has(idx) ? 'rotate-180' : ''}`} />
                          </div>
                        </div>

                        {expandedTools.has(idx) && (
                          <div className="border-t border-[rgba(255,255,255,0.06)] bg-black/20">
                            <div className="p-4">
                              <div className="text-[11px] font-semibold text-white/40 uppercase tracking-[0.8px] mb-3">
                                Details
                              </div>
                              
                              <div className="space-y-3">
                                <div>
                                  <div className="text-[11px] font-semibold text-white/50 font-mono uppercase tracking-[0.5px] mb-1.5">
                                    Description
                                  </div>
                                  <div className="text-[13px] text-white/90 font-mono px-3 py-2 bg-[rgba(255,255,255,0.02)] rounded-md border border-[rgba(255,255,255,0.04)]">
                                    {activity.description}
                                  </div>
                                </div>
                                
                                {activity.filePath && (
                                  <div>
                                    <div className="text-[11px] font-semibold text-white/50 font-mono uppercase tracking-[0.5px] mb-1.5">
                                      File Path
                                    </div>
                                    <div className="text-[13px] text-white/90 font-mono px-3 py-2 bg-[rgba(255,255,255,0.02)] rounded-md border border-[rgba(255,255,255,0.04)] break-all">
                                      {activity.filePath}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
