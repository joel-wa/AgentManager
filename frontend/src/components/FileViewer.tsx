import { useState, useEffect } from 'react'
import { X, Save, Copy, Download, FileText, FileCode, FileJson, Image, ExternalLink } from 'lucide-react'

type Props = {
  filePath: string
  fileName: string
  content: string
  isLoading?: boolean
  onClose: () => void
  onSave?: (content: string) => void
  readOnly?: boolean
}

export function FileViewer({ filePath, fileName, content, isLoading, onClose, onSave, readOnly = false }: Props) {
  const [editedContent, setEditedContent] = useState(content)
  const [hasChanges, setHasChanges] = useState(false)
  const [copied, setCopied] = useState(false)

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

  const handleDownload = () => {
    const blob = new Blob([editedContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleOpenWith = () => {
    // Note: Creates a blob with application/octet-stream type and triggers download.
    // Browser behavior varies: most browsers will download the file, which can then be 
    // opened with the user's preferred application. True "Open With" dialog depends on 
    // OS/browser integration and may require desktop application support.
    const blob = new Blob([editedContent], { type: 'application/octet-stream' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName
    a.click()
    URL.revokeObjectURL(url)
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

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-dark-surface rounded-xl shadow-2xl w-full max-w-4xl h-[80vh] mx-4 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-border">
          <div className="flex items-center gap-3">
            {getFileIcon()}
            <div>
              <h2 className="text-lg font-semibold text-white">{fileName}</h2>
              <p className="text-xs text-gray-500">{filePath}</p>
            </div>
            {hasChanges && (
              <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded">
                Unsaved changes
              </span>
            )}
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={handleOpenWith}
              className="flex items-center gap-1.5 px-3 py-1.5 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors text-sm"
              title="Open with external application"
            >
              <ExternalLink className="w-4 h-4" />
              Open With
            </button>
            
            <div className="w-px h-6 bg-dark-border" />
            
            <button
              onClick={handleCopy}
              className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
              title="Copy to clipboard"
            >
              <Copy className="w-4 h-4" />
            </button>
            {copied && <span className="text-xs text-green-400">Copied!</span>}
            
            <button
              onClick={handleDownload}
              className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
              title="Download file"
            >
              <Download className="w-4 h-4" />
            </button>
            
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
                Save
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
