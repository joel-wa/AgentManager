import { useState, useEffect } from 'react'
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
  Search,
  RefreshCw,
  AlertCircle
} from 'lucide-react'
import { api, FileItem as ApiFileItem } from '../services/api'

export type FileItem = {
  name: string
  type: 'file' | 'folder'
  extension?: string
  children?: FileItem[]
  summary?: string
  path?: string
}

type Props = {
  projectId?: string
  onFileSelect?: (file: FileItem, fullPath: string) => void
}

// Mock data for when backend is not available
const mockFileTree: FileItem[] = [
  {
    name: 'auth',
    type: 'folder',
    path: 'auth',
    children: [
      { name: 'strategy.md', type: 'file', extension: 'md', summary: 'OAuth 2.0 implementation strategy', path: 'auth/strategy.md' },
      { name: 'tokens.md', type: 'file', extension: 'md', summary: 'JWT token handling guide', path: 'auth/tokens.md' },
    ]
  },
  {
    name: 'notes',
    type: 'folder',
    path: 'notes',
    children: [
      { name: 'session_summary.md', type: 'file', extension: 'md', summary: 'Today\'s session notes', path: 'notes/session_summary.md' },
      { name: 'research_topics.md', type: 'file', extension: 'md', path: 'notes/research_topics.md' },
    ]
  },
  {
    name: 'api',
    type: 'folder',
    path: 'api',
    children: [
      { name: 'endpoints.json', type: 'file', extension: 'json', path: 'api/endpoints.json' },
      { name: 'schema.ts', type: 'file', extension: 'ts', path: 'api/schema.ts' },
    ]
  },
  { name: 'README.md', type: 'file', extension: 'md', summary: 'Project overview and quick start', path: 'README.md' },
  { name: 'config.json', type: 'file', extension: 'json', path: 'config.json' },
]

export function FileBrowser({ projectId, onFileSelect }: Props) {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedFile, setSelectedFile] = useState<string | null>(null)
  const [fileTree, setFileTree] = useState<FileItem[]>(mockFileTree)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (projectId) {
      loadFiles()
    }
  }, [projectId])

  const loadFiles = async () => {
    if (!projectId) return
    
    setIsLoading(true)
    setError(null)
    try {
      const files = await api.listFiles(projectId)
      if (files && files.length > 0) {
        setFileTree(convertApiFiles(files))
      } else {
        // Empty project - clear mock data
        setFileTree([])
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Backend not available'
      console.error('Failed to load files:', errorMessage)
      setError(errorMessage)
      // Keep mock data on error for demo purposes
    } finally {
      setIsLoading(false)
    }
  }

  const convertApiFiles = (apiFiles: ApiFileItem[], parentPath: string = ''): FileItem[] => {
    return apiFiles.map(file => {
      const fullPath = parentPath ? `${parentPath}/${file.name}` : file.name
      return {
        name: file.name,
        type: file.type,
        extension: file.extension,
        summary: file.summary,
        path: fullPath,
        children: file.children ? convertApiFiles(file.children, fullPath) : undefined
      }
    })
  }

  const handleFileClick = (item: FileItem) => {
    setSelectedFile(item.path || item.name)
    if (item.type === 'file' && onFileSelect) {
      onFileSelect(item, item.path || item.name)
    }
  }

  const filterFiles = (items: FileItem[]): FileItem[] => {
    if (!searchQuery) return items
    
    return items.reduce<FileItem[]>((acc, item) => {
      if (item.name.toLowerCase().includes(searchQuery.toLowerCase())) {
        acc.push(item)
      } else if (item.children) {
        const filteredChildren = filterFiles(item.children)
        if (filteredChildren.length > 0) {
          acc.push({ ...item, children: filteredChildren })
        }
      }
      return acc
    }, [])
  }
  
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
          <div className="flex items-center gap-1">
            <button 
              onClick={loadFiles}
              className="p-1 hover:bg-dark-hover rounded transition-colors" 
              title="Refresh"
            >
              <RefreshCw className={`w-3 h-3 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button className="p-1 hover:bg-dark-hover rounded transition-colors" title="New file">
              <Plus className="w-3 h-3" />
            </button>
          </div>
        </div>
        
        {error && (
          <div className="flex items-center gap-2 px-2 py-2 text-xs text-yellow-400">
            <AlertCircle className="w-3 h-3" />
            <span>{error}</span>
          </div>
        )}
        
        {filterFiles(fileTree).map((item, idx) => (
          <FileTreeItem 
            key={idx} 
            item={item} 
            depth={0}
            selectedFile={selectedFile}
            onSelect={handleFileClick}
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
  onSelect: (item: FileItem) => void
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
      case 'py': return <FileCode className="w-4 h-4 text-blue-500" />
      case 'rs': return <FileCode className="w-4 h-4 text-orange-400" />
      default: return <FileText className="w-4 h-4 text-gray-400" />
    }
  }
  
  const isSelected = selectedFile === (item.path || item.name)
  
  return (
    <div>
      <div
        className={`flex items-center gap-1 px-2 py-1 cursor-pointer rounded-md transition-colors group
          ${isSelected ? 'bg-accent-blue/20 text-white' : 'hover:bg-dark-hover text-gray-300'}`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={() => {
          if (item.type === 'folder') {
            setIsOpen(!isOpen)
          }
          onSelect(item)
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
