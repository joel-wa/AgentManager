import { useState, useEffect, useRef } from 'react'
import { X, Search, FileText } from 'lucide-react'

const MAX_SEARCH_RESULTS = 50

type Props = {
  isOpen: boolean
  onClose: () => void
  availableFiles: string[]
  onFileSelect: (filePath: string) => void
}

export function SearchModal({ isOpen, onClose, availableFiles, onFileSelect }: Props) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const modalRef = useRef<HTMLDivElement>(null)

  // Filter files based on search query
  const filteredFiles = availableFiles.filter(file =>
    file.toLowerCase().includes(searchQuery.toLowerCase())
  ).slice(0, MAX_SEARCH_RESULTS) // Limit results for performance

  // Reset selected index when search changes
  useEffect(() => {
    setSelectedIndex(0)
  }, [searchQuery])

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen) {
      setSearchQuery('')
      setSelectedIndex(0)
      inputRef.current?.focus()
    }
  }, [isOpen])

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return

      if (e.key === 'ArrowDown') {
        e.preventDefault()
        setSelectedIndex(prev =>
          prev < filteredFiles.length - 1 ? prev + 1 : prev
        )
      } else if (e.key === 'ArrowUp') {
        e.preventDefault()
        setSelectedIndex(prev => prev > 0 ? prev - 1 : prev)
      } else if (e.key === 'Enter') {
        e.preventDefault()
        if (filteredFiles.length > 0) {
          handleSelect(filteredFiles[selectedIndex])
        }
      } else if (e.key === 'Escape') {
        e.preventDefault()
        onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, filteredFiles, selectedIndex])

  // Auto-scroll selected item into view
  useEffect(() => {
    const selectedElement = modalRef.current?.querySelector(`[data-index="${selectedIndex}"]`)
    if (selectedElement) {
      selectedElement.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  }, [selectedIndex])

  const handleSelect = (filePath: string) => {
    onFileSelect(filePath)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center pt-[15vh]"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div className="bg-[#2a2a2a] border border-[rgba(255,255,255,0.12)] rounded-2xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden">
        {/* Search Header */}
        <div className="flex items-center gap-3 px-4 py-3 border-b border-[rgba(255,255,255,0.08)]">
          <Search className="w-5 h-5 text-white/50" />
          <input
            ref={inputRef}
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search files... (type to filter)"
            className="flex-1 bg-transparent border-none text-white text-base placeholder-white/40 outline-none"
          />
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center text-white/50 hover:text-white/90 hover:bg-white/8 rounded-lg transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Results List */}
        <div
          ref={modalRef}
          className="max-h-[60vh] overflow-y-auto"
        >
          {filteredFiles.length === 0 ? (
            <div className="px-4 py-12 text-center text-white/40">
              {searchQuery ? 'No files found matching your search' : 'Start typing to search files...'}
            </div>
          ) : (
            <div className="py-2">
              {filteredFiles.map((file, index) => (
                <button
                  key={file}
                  data-index={index}
                  onClick={() => handleSelect(file)}
                  className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors
                    ${index === selectedIndex
                      ? 'bg-blue-500/20 border-l-2 border-blue-500'
                      : 'hover:bg-white/5'
                    }`}
                >
                  <FileText className="w-4 h-4 text-blue-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-white/90 truncate font-mono">
                      {file}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t border-[rgba(255,255,255,0.08)] bg-[rgba(0,0,0,0.2)]">
          <div className="flex items-center gap-4 text-xs text-white/40">
            <span>
              <kbd className="px-1.5 py-0.5 bg-white/8 rounded text-[10px]">↑↓</kbd> Navigate
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 bg-white/8 rounded text-[10px]">Enter</kbd> Open
            </span>
            <span>
              <kbd className="px-1.5 py-0.5 bg-white/8 rounded text-[10px]">Esc</kbd> Close
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
