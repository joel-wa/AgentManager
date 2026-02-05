import { useState } from 'react'
import { FileText, History, AlertCircle, ChevronDown, ChevronRight } from 'lucide-react'
import type { FileChange } from '../App'
import { FileVersionHistory } from './FileVersionHistory'

type Props = {
  fileChanges: FileChange[]
  projectId?: string
  onVersionRestore?: (filePath: string, version: number) => void
}

export function FileChangesList({ fileChanges, projectId, onVersionRestore }: Props) {
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set())
  const [viewingVersions, setViewingVersions] = useState<{ path: string; name: string } | null>(null)
  
  // Use fileChanges length as refresh key - changes when new file changes arrive
  const refreshKey = fileChanges.length

  if (fileChanges.length === 0) return null

  const toggleFile = (path: string) => {
    const newExpanded = new Set(expandedFiles)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpandedFiles(newExpanded)
  }

  const handleViewVersions = (path: string) => {
    const fileName = path.split('/').pop() || path
    setViewingVersions({ path, name: fileName })
  }

  const handleVersionRestore = (version: number) => {
    if (viewingVersions) {
      onVersionRestore?.(viewingVersions.path, version)
      setViewingVersions(null)
    }
  }

  if (viewingVersions && projectId) {
    return (
      <div className="mt-3 border border-dark-border rounded-lg overflow-hidden bg-dark-bg">
        <FileVersionHistory
          projectId={projectId}
          filePath={viewingVersions.path}
          fileName={viewingVersions.name}
          onRestore={handleVersionRestore}
          onClose={() => setViewingVersions(null)}
          refreshKey={refreshKey}
        />
      </div>
    )
  }

  return (
    <div className="mt-3 border border-dark-border rounded-lg overflow-hidden bg-dark-bg">
      <div className="flex items-center gap-2 px-3 py-2 bg-dark-surface border-b border-dark-border">
        <FileText className="w-4 h-4 text-accent-orange" />
        <span className="text-sm font-medium text-white">
          File Changes ({fileChanges.length})
        </span>
      </div>
      
      <div className="divide-y divide-dark-border">
        {fileChanges.map((change, idx) => {
          const isExpanded = expandedFiles.has(change.path)
          const fileName = change.path.split('/').pop() || change.path
          
          return (
            <div key={idx} className="bg-dark-surface">
              <div
                className="flex items-center justify-between p-3 cursor-pointer hover:bg-dark-hover transition-colors"
                onClick={() => toggleFile(change.path)}
              >
                <div className="flex items-center gap-2 flex-1 min-w-0">
                  <button className="text-gray-400 hover:text-white transition-colors flex-shrink-0">
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </button>
                  <FileText className="w-4 h-4 text-accent-blue flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white truncate">{fileName}</p>
                    <p className="text-xs text-gray-500 truncate">{change.path}</p>
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded flex-shrink-0 ${
                    change.action === 'modified' 
                      ? 'bg-accent-orange/20 text-accent-orange'
                      : change.action === 'created'
                      ? 'bg-accent-green/20 text-accent-green'
                      : 'bg-red-500/20 text-red-400'
                  }`}>
                    {change.action}
                  </span>
                </div>
              </div>

              {isExpanded && projectId && (
                <div className="px-3 pb-3 border-t border-dark-border bg-dark-bg">
                  <div className="pt-3 space-y-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleViewVersions(change.path)
                      }}
                      className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-accent-blue hover:bg-accent-blue/80 text-white rounded text-sm transition-colors"
                    >
                      <History className="w-4 h-4" />
                      View Version History
                    </button>
                    
                    <div className="text-xs text-gray-400 space-y-1 pt-2">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                        <p>
                          The previous version of this file has been automatically saved. 
                          You can restore it at any time from the version history.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
