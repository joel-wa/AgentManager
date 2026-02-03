import { useState, useEffect } from 'react'
import { X, Save, Copy, FileText, FileCode, FileJson, Image, Eye, Code } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'

type Props = {
  filePath: string
  fileName: string
  content: string
  isLoading?: boolean
  onClose: () => void
  onSave?: (content: string) => void
  readOnly?: boolean
  asSidePanel?: boolean
}

export function FileViewer({ filePath, fileName, content, isLoading, onClose, onSave, readOnly = false, asSidePanel = false }: Props) {
  const [editedContent, setEditedContent] = useState(content)
  const [hasChanges, setHasChanges] = useState(false)
  const [copied, setCopied] = useState(false)
  const [viewMode, setViewMode] = useState<'edit' | 'preview'>('preview')

  const isMarkdown = fileName.endsWith('.md')

  useEffect(() => {
    setEditedContent(content)
    setHasChanges(false)
  }, [content])

  const handleContentChange = (newContent: string) => {
    setEditedContent(newContent)
    setHasChanges(newContent !== content)
  }

  const handleSave = () => {
    if (onSave && hasChanges) {
      onSave(editedContent)
      setHasChanges(false)
    }
  }

  const handleCopy = async () => {
    await navigator.clipboard.writeText(editedContent)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const getFileIcon = () => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'md': return <FileText className="w-5 h-5 text-blue-400" />
      case 'ts':
      case 'tsx':
      case 'js':
      case 'jsx':
      case 'py':
      case 'rs': return <FileCode className="w-5 h-5 text-yellow-400" />
      case 'json': return <FileJson className="w-5 h-5 text-green-400" />
      case 'png':
      case 'jpg':
      case 'svg': return <Image className="w-5 h-5 text-purple-400" />
      default: return <FileText className="w-5 h-5 text-gray-400" />
    }
  }

  const getLanguage = () => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    const langMap: Record<string, string> = {
      'ts': 'typescript',
      'tsx': 'typescript',
      'js': 'javascript',
      'jsx': 'javascript',
      'py': 'python',
      'rs': 'rust',
      'json': 'json',
      'md': 'markdown',
      'html': 'html',
      'css': 'css',
    }
    return langMap[ext || ''] || 'plaintext'
  }

  const containerClass = asSidePanel 
    ? "h-full flex flex-col bg-dark-surface border-l border-dark-border"
    : "fixed inset-0 bg-black/60 flex items-center justify-center z-50"

  const innerClass = asSidePanel
    ? "h-full flex flex-col"
    : "bg-dark-surface rounded-xl shadow-2xl w-full max-w-4xl h-[80vh] mx-4 flex flex-col"

  return (
    <div className={containerClass}>
      <div className={innerClass}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-border">
          <div className="flex items-center gap-3 min-w-0">
            {getFileIcon()}
            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-white truncate">{fileName}</h2>
              <p className="text-xs text-gray-500 truncate">{filePath}</p>
            </div>
            {hasChanges && (
              <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded">
                Unsaved
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            {isMarkdown && (
              <>
                <button
                  onClick={() => setViewMode('preview')}
                  className={`p-2 rounded-lg transition-colors ${
                    viewMode === 'preview' 
                      ? 'bg-accent-blue text-white' 
                      : 'text-gray-400 hover:text-white hover:bg-dark-hover'
                  }`}
                  title="Preview mode"
                >
                  <Eye className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('edit')}
                  className={`p-2 rounded-lg transition-colors ${
                    viewMode === 'edit' 
                      ? 'bg-accent-blue text-white' 
                      : 'text-gray-400 hover:text-white hover:bg-dark-hover'
                  }`}
                  title="Edit mode"
                >
                  <Code className="w-4 h-4" />
                </button>
                <div className="w-px h-6 bg-dark-border" />
              </>
            )}
            
            <button
              onClick={handleCopy}
              className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
              title="Copy to clipboard"
            >
              <Copy className="w-4 h-4" />
            </button>
            {copied && <span className="text-xs text-green-400">Copied!</span>}
            
            {!readOnly && onSave && (
              <button
                onClick={handleSave}
                disabled={!hasChanges}
                className={`flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors
                  ${hasChanges 
                    ? 'bg-accent-blue text-white hover:bg-blue-600' 
                    : 'bg-dark-hover text-gray-500 cursor-not-allowed'
                  }`}
                title="Save changes"
              >
                <Save className="w-4 h-4" />
              </button>
            )}
            
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="animate-spin w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full" />
            </div>
          ) : isMarkdown && viewMode === 'preview' ? (
            <div className="h-full overflow-y-auto p-6 prose prose-invert prose-sm max-w-none">
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
                  code: ({node, className, children, ...props}) => {
                    const match = /language-(\w+)/.exec(className || '')
                    const isInline = !match
                    return isInline ? 
                      <code className="bg-gray-800 px-1 py-0.5 rounded text-sm" {...props}>{children}</code> :
                      <code className="block bg-gray-800 p-3 rounded my-2 overflow-x-auto" {...props}>{children}</code>
                  },
                  pre: ({node, ...props}) => (
                    <pre className="bg-gray-800 p-3 rounded my-2 overflow-x-auto" {...props} />
                  ),
                }}
              >
                {editedContent}
              </ReactMarkdown>
            </div>
          ) : (
            <textarea
              value={editedContent}
              onChange={(e) => handleContentChange(e.target.value)}
              readOnly={readOnly}
              className={`w-full h-full p-4 bg-dark-bg text-gray-200 font-mono text-sm resize-none
                focus:outline-none ${readOnly ? 'cursor-default' : ''}`}
              style={{ tabSize: 2 }}
              spellCheck={false}
            />
          )}
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between px-4 py-2 border-t border-dark-border text-xs text-gray-500">
          <span>Language: {getLanguage()}</span>
          <span>{editedContent.split('\n').length} lines</span>
        </div>
      </div>
    </div>
  )
}
