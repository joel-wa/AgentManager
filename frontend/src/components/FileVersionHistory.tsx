import { useState, useEffect } from 'react'
import { History, Check, X, ChevronDown, ChevronRight, Clock, FileText, AlertCircle, RefreshCw } from 'lucide-react'
import type { VersionHistory, VersionMetadata } from '../services/api'
import { api } from '../services/api'

type Props = {
  projectId: string
  filePath: string
  fileName: string
  onRestore?: (version: number) => void
  onClose?: () => void
  refreshKey?: string | number  // Trigger refresh when this changes
}

export function FileVersionHistory({ projectId, filePath, fileName, onRestore, onClose, refreshKey }: Props) {
  const [history, setHistory] = useState<VersionHistory | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedVersions, setExpandedVersions] = useState<Set<number>>(new Set())
  const [restoringVersion, setRestoringVersion] = useState<number | null>(null)
  const [showConfirm, setShowConfirm] = useState<number | null>(null)

  useEffect(() => {
    loadVersionHistory()
  }, [projectId, filePath, refreshKey])

  const loadVersionHistory = async () => {
    setLoading(true)
    setError(null)
    try {
      console.log('[FileVersionHistory] Fetching version history for:', {
        projectId,
        filePath,
        url: `http://localhost:8000/api/projects/${projectId}/versions/${encodeURIComponent(filePath)}`
      })
      const data = await api.listFileVersions(projectId, filePath)
      console.log('[FileVersionHistory] Loaded version history:', {
        filePath,
        currentVersion: data.current_version,
        totalVersions: data.versions.length,
        versions: data.versions
      })
      setHistory(data)
    } catch (err) {
      console.error('[FileVersionHistory] Error loading version history:', err)
      setError(err instanceof Error ? err.message : 'Failed to load version history')
    } finally {
      setLoading(false)
    }
  }

  const handleRestore = async (version: number) => {
    setRestoringVersion(version)
    try {
      await api.restoreFileVersion(projectId, filePath, version)
      
      // Reload version history
      await loadVersionHistory()
      
      // Notify parent
      onRestore?.(version)
      
      // Clear confirmation
      setShowConfirm(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to restore version')
    } finally {
      setRestoringVersion(null)
    }
  }

  const toggleExpanded = (version: number) => {
    const newExpanded = new Set(expandedVersions)
    if (newExpanded.has(version)) {
      newExpanded.delete(version)
    } else {
      newExpanded.add(version)
    }
    setExpandedVersions(newExpanded)
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    return date.toLocaleString([], { 
      month: 'short', 
      day: 'numeric', 
      hour: '2-digit', 
      minute: '2-digit' 
    })
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (loading) {
    return (
      <div className="p-4 text-center text-gray-400">
        <div className="animate-spin w-6 h-6 border-2 border-accent-blue border-t-transparent rounded-full mx-auto mb-2" />
        <p className="text-sm">Loading version history...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="text-red-400 font-medium mb-1">Error Loading Versions</h3>
              <p className="text-sm text-red-300/80">{error}</p>
              <button
                onClick={loadVersionHistory}
                className="mt-3 px-3 py-1.5 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded text-sm transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  if (!history || history.versions.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
        <p className="text-sm">No version history available</p>
        <p className="text-xs mt-1">Changes will be tracked after the first modification</p>
      </div>
    )
  }

  return (
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-gray-400">
          <History className="w-4 h-4" />
          <span className="text-sm font-medium">Version History</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadVersionHistory}
            disabled={loading}
            className="p-1.5 hover:bg-dark-hover rounded transition-colors disabled:opacity-50 group"
            title="Refresh version history"
          >
            <RefreshCw className={`w-4 h-4 text-gray-400 group-hover:text-white transition-colors ${loading ? 'animate-spin' : ''}`} />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-1 hover:bg-dark-hover rounded transition-colors"
            >
              <X className="w-4 h-4 text-gray-400" />
            </button>
          )}
        </div>
      </div>

      <div className="mb-4 p-3 bg-dark-surface rounded-lg">
        <h3 className="text-white font-medium text-sm mb-1">{fileName}</h3>
        <p className="text-xs text-gray-500">{filePath}</p>
        <p className="text-xs text-gray-400 mt-2">
          Current version: <span className="text-accent-blue">v{history.current_version}</span>
        </p>
      </div>

      <div className="space-y-2">
        {history.versions.slice().reverse().map((version: VersionMetadata) => {
          const isExpanded = expandedVersions.has(version.version)
          const isCurrent = version.version === history.current_version
          const isRestoring = restoringVersion === version.version
          const showConfirmDialog = showConfirm === version.version

          return (
            <div
              key={version.version}
              className={`bg-dark-surface rounded-lg overflow-hidden transition-all ${
                isCurrent ? 'ring-2 ring-accent-blue/30' : ''
              }`}
            >
              <div
                className="p-3 cursor-pointer hover:bg-dark-hover transition-colors"
                onClick={() => toggleExpanded(version.version)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3 flex-1">
                    <button className="text-gray-400 hover:text-white transition-colors mt-0.5">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-white font-medium text-sm">
                          Version {version.version}
                        </span>
                        {isCurrent && (
                          <span className="text-xs bg-accent-blue/20 text-accent-blue px-2 py-0.5 rounded">
                            Current
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDate(version.timestamp)}
                        </span>
                        <span>{formatSize(version.file_size)}</span>
                      </div>
                      {version.message && (
                        <p className="text-xs text-gray-500 mt-1 italic">"{version.message}"</p>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="px-3 pb-3 border-t border-dark-border">
                  <div className="mt-3 space-y-2">
                    <div className="text-xs text-gray-400">
                      <div className="flex justify-between py-1">
                        <span>Content Hash:</span>
                        <span className="font-mono text-gray-500">
                          {version.content_hash.substring(0, 16)}...
                        </span>
                      </div>
                    </div>

                    {!isCurrent && (
                      <div className="pt-2">
                        {showConfirmDialog ? (
                          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded p-3">
                            <p className="text-sm text-yellow-300 mb-3">
                              Are you sure you want to restore to version {version.version}? 
                              Your current version will be saved before restoring.
                            </p>
                            <div className="flex gap-2">
                              <button
                                onClick={() => handleRestore(version.version)}
                                disabled={isRestoring}
                                className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 bg-accent-green hover:bg-accent-green/80 text-white rounded text-sm transition-colors disabled:opacity-50"
                              >
                                <Check className="w-4 h-4" />
                                {isRestoring ? 'Restoring...' : 'Confirm'}
                              </button>
                              <button
                                onClick={() => setShowConfirm(null)}
                                disabled={isRestoring}
                                className="flex-1 flex items-center justify-center gap-2 px-3 py-1.5 bg-dark-hover hover:bg-dark-border text-gray-300 rounded text-sm transition-colors"
                              >
                                <X className="w-4 h-4" />
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setShowConfirm(version.version)
                            }}
                            className="w-full flex items-center justify-center gap-2 px-3 py-1.5 bg-accent-blue hover:bg-accent-blue/80 text-white rounded text-sm transition-colors"
                          >
                            <History className="w-4 h-4" />
                            Restore This Version
                          </button>
                        )}
                      </div>
                    )}
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
