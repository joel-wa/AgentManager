import { useState } from 'react'
import { Clock, FileText, PenTool, History, ChevronDown, ChevronRight } from 'lucide-react'
import type { TimelineEntry } from '../App'
import { FileVersionHistory } from './FileVersionHistory'

type Props = {
  entries: TimelineEntry[]
  projectId?: string
  onVersionRestore?: (filePath: string, version: number) => void
}

export function Timeline({ entries, projectId, onVersionRestore }: Props) {
  const [expandedEntries, setExpandedEntries] = useState<Set<string>>(new Set())
  const [viewingVersions, setViewingVersions] = useState<{ path: string; name: string } | null>(null)

  // Use entries length as refresh key - triggers version history refresh when new entries added
  const refreshKey = entries.length

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'read': return <FileText className="w-3 h-3 text-accent-green" />
      case 'write': 
      case 'modified': 
        return <PenTool className="w-3 h-3 text-accent-orange" />
      default: return <FileText className="w-3 h-3 text-gray-400" />
    }
  }

  const toggleEntry = (entryId: string) => {
    const newExpanded = new Set(expandedEntries)
    if (newExpanded.has(entryId)) {
      newExpanded.delete(entryId)
    } else {
      newExpanded.add(entryId)
    }
    setExpandedEntries(newExpanded)
  }

  const handleViewVersions = (filePath: string) => {
    const fileName = filePath.split('/').pop() || filePath
    setViewingVersions({ path: filePath, name: fileName })
  }

  const handleVersionRestore = (version: number) => {
    if (viewingVersions) {
      onVersionRestore?.(viewingVersions.path, version)
      setViewingVersions(null)
    }
  }

  if (viewingVersions && projectId) {
    return (
      <FileVersionHistory
        projectId={projectId}
        filePath={viewingVersions.path}
        fileName={viewingVersions.name}
        onRestore={handleVersionRestore}
        onClose={() => setViewingVersions(null)}
        refreshKey={refreshKey}
      />
    )
  }

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-4 text-gray-400">
        <Clock className="w-4 h-4" />
        <span className="text-sm font-medium">Git Commit History</span>
      </div>
      
      <div className="space-y-4">
        {entries.map(entry => {
          const isExpanded = expandedEntries.has(entry.id)
          const writtenFiles = entry.files.filter(f => f.action === 'write' || f.action === 'modified')
          
          return (
            <div key={entry.id} className="relative pl-6 border-l border-dark-border">
              <div className="absolute left-0 top-0 w-3 h-3 -translate-x-1.5 bg-dark-bg border-2 border-accent-blue rounded-full" />
              
              <div className="bg-dark-surface rounded-lg overflow-hidden">
                <div 
                  className="p-3 hover:bg-dark-hover transition-colors cursor-pointer"
                  onClick={() => toggleEntry(entry.id)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 flex-1">
                      <button className="text-gray-400 hover:text-white transition-colors">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                      </button>
                      <span className="text-sm font-medium text-white">{entry.title}</span>
                    </div>
                    <span className="text-xs text-gray-500">{formatTime(entry.timestamp)}</span>
                  </div>
                  
                  {!isExpanded && (
                    <div className="flex items-center gap-2 text-xs text-gray-400 ml-6">
                      <span>{entry.files.length} file{entry.files.length !== 1 ? 's' : ''}</span>
                      {writtenFiles.length > 0 && (
                        <span className="text-accent-orange">
                          • {writtenFiles.length} modified
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {isExpanded && (
                  <div className="px-3 pb-3 border-t border-dark-border">
                    <div className="space-y-2 mt-3">
                      {entry.files.map((file, idx) => {
                        const canViewVersions = (file.action === 'write' || file.action === 'modified') && projectId
                        
                        return (
                          <div
                            key={idx}
                            className="flex items-center justify-between gap-2 p-2 rounded bg-dark-bg hover:bg-dark-hover transition-colors"
                          >
                            <div className="flex items-center gap-2 text-sm text-gray-400 flex-1 min-w-0">
                              {getActionIcon(file.action)}
                              <span className="capitalize text-xs text-gray-500 flex-shrink-0">
                                {file.action}:
                              </span>
                              <span className="text-accent-blue truncate">{file.path}</span>
                            </div>
                            
                            {canViewVersions && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleViewVersions(file.path)
                                }}
                                className="flex items-center gap-1 px-2 py-1 text-xs bg-accent-blue/20 hover:bg-accent-blue/30 text-accent-blue rounded transition-colors flex-shrink-0"
                              >
                                <History className="w-3 h-3" />
                                Versions
                              </button>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )
        })}
        
        {entries.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No commits yet</p>
            <p className="text-xs">Git commits will appear here as files are modified</p>
          </div>
        )}
      </div>
    </div>
  )
}
