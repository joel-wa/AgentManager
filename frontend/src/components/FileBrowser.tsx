import { useState } from 'react'
import { 
  Folder, 
  FileText, 
  ChevronRight, 
  ChevronDown,
  FileCode,
  FileJson,
  Image,
  MoreVertical,
  Plus,
  Search
} from 'lucide-react'

type FileItem = {
  name: string
  type: 'file' | 'folder'
  extension?: string
  children?: FileItem[]
  summary?: string
}

const mockFileTree: FileItem[] = [
  {
    name: 'auth',
    type: 'folder',
    children: [
      { name: 'strategy.md', type: 'file', extension: 'md', summary: 'OAuth 2.0 implementation strategy' },
      { name: 'tokens.md', type: 'file', extension: 'md', summary: 'JWT token handling guide' },
    ]
  },
  {
    name: 'notes',
    type: 'folder',
    children: [
      { name: 'session_summary.md', type: 'file', extension: 'md', summary: 'Today\'s session notes' },
      { name: 'research_topics.md', type: 'file', extension: 'md' },
    ]
  },
  {
    name: 'api',
    type: 'folder',
    children: [
      { name: 'endpoints.json', type: 'file', extension: 'json' },
      { name: 'schema.ts', type: 'file', extension: 'ts' },
    ]
  },
  { name: 'README.md', type: 'file', extension: 'md', summary: 'Project overview and quick start' },
  { name: 'config.json', type: 'file', extension: 'json' },
]

export function FileBrowser() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  
  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b border-dark-border">
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            type="text"
            placeholder="Search files..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full bg-dark-surface border border-dark-border rounded-md pl-9 pr-3 py-2 
              text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue"
          />
        </div>
      </div>
      
      {/* File Tree */}
      <div className="flex-1 overflow-auto p-2">
        <div className="flex items-center justify-between px-2 py-1 text-xs text-gray-400 uppercase">
          <span>Explorer</span>
          <button className="p-1 hover:bg-dark-hover rounded transition-colors" title="New file">
            <Plus className="w-3 h-3" />
          </button>
        </div>
        
        {mockFileTree.map((item, idx) => (
          <FileTreeItem 
            key={idx} 
            item={item} 
            depth={0}
            selectedFile={selectedFile}
            onSelect={setSelectedFile}
          />
        ))}
      </div>
    </div>
  )
}

type FileTreeItemProps = {
  item: FileItem
  depth: number
  selectedFile: string | null
  onSelect: (path: string) => void
}

function FileTreeItem({ item, depth, selectedFile, onSelect }: FileTreeItemProps) {
  const [isOpen, setIsOpen] = useState(depth === 0)
  const [showTooltip, setShowTooltip] = useState(false)
  
  const getFileIcon = () => {
    if (item.type === 'folder') {
      return isOpen ? <Folder className="w-4 h-4 text-accent-orange" /> : <Folder className="w-4 h-4 text-accent-orange" />
    }
    
    switch (item.extension) {
      case 'md': return <FileText className="w-4 h-4 text-blue-400" />
      case 'ts':
      case 'tsx':
      case 'js':
      case 'jsx': return <FileCode className="w-4 h-4 text-yellow-400" />
      case 'json': return <FileJson className="w-4 h-4 text-green-400" />
      case 'png':
      case 'jpg':
      case 'svg': return <Image className="w-4 h-4 text-purple-400" />
      default: return <FileText className="w-4 h-4 text-gray-400" />
    }
  }
  
  const isSelected = selectedFile === item.name
  
  return (
    <div>
      <div
        className={`flex items-center gap-1 px-2 py-1 cursor-pointer rounded-md transition-colors
          ${isSelected ? 'bg-accent-blue/20 text-white' : 'hover:bg-dark-hover text-gray-300'}`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => {
          if (item.type === 'folder') {
            setIsOpen(!isOpen)
          } else {
            onSelect(item.name)
          }
        }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {item.type === 'folder' && (
          <span className="text-gray-500">
            {isOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </span>
        )}
        {item.type === 'file' && <span className="w-3" />}
        
        {getFileIcon()}
        <span className="text-sm flex-1 truncate">{item.name}</span>
        
        <button 
          className="p-1 opacity-0 group-hover:opacity-100 hover:bg-dark-border rounded transition-all"
          onClick={e => { e.stopPropagation() }}
        >
          <MoreVertical className="w-3 h-3 text-gray-500" />
        </button>
      </div>
      
      {/* Tooltip with summary */}
      {showTooltip && item.summary && (
        <div className="absolute z-10 ml-4 px-2 py-1 bg-dark-surface border border-dark-border rounded text-xs text-gray-300 max-w-xs">
          {item.summary}
        </div>
      )}
      
      {item.type === 'folder' && isOpen && item.children && (
        <div>
          {item.children.map((child, idx) => (
            <FileTreeItem 
              key={idx} 
              item={child} 
              depth={depth + 1}
              selectedFile={selectedFile}
              onSelect={onSelect}
            />
          ))}
        </div>
      )}
    </div>
  )
}
