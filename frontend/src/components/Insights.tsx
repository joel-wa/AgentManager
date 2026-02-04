import { Lightbulb, AlertTriangle, Sparkles, GitMerge, Check, X, RefreshCw, Loader2 } from 'lucide-react'
import type { Suggestion } from '../App'
import { useState } from 'react'

type Props = {
  suggestions: Suggestion[]
  onAccept: (id: string) => Promise<{ success: boolean; changes?: string[]; error?: string }>
  onDismiss: (id: string) => Promise<void>
  onTrigger?: (customMessage?: string) => Promise<void>
  projectId?: string
  isProcessing?: boolean
}

export function Insights({ suggestions, onAccept, onDismiss, onTrigger, projectId, isProcessing }: Props) {
  const [isTriggering, setIsTriggering] = useState(false)
  const [customMessage, setCustomMessage] = useState('')
  const [processingId, setProcessingId] = useState<string | null>(null)
  const [executionResult, setExecutionResult] = useState<{
    suggestionId: string
    success: boolean
    changes?: string[]
    error?: string
  } | null>(null)
  
  const handleTrigger = async () => {
    if (!onTrigger || isTriggering || isProcessing) return
    setIsTriggering(true)
    try {
      await onTrigger(customMessage.trim() || undefined)
      setCustomMessage('') // Clear after successful trigger
    } finally {
      setIsTriggering(false)
    }
  }

  const handleAccept = async (suggestionId: string) => {
    if (isProcessing || processingId) return
    
    setProcessingId(suggestionId)
    setExecutionResult(null)
    
    try {
      const result = await onAccept(suggestionId)
      setExecutionResult({
        suggestionId,
        ...result
      })
    } finally {
      setProcessingId(null)
    }
  }

  const handleDismiss = async (suggestionId: string) => {
    if (isProcessing || processingId) return
    
    setProcessingId(suggestionId)
    try {
      await onDismiss(suggestionId)
    } finally {
      setProcessingId(null)
    }
  }
  
  const getTypeIcon = (type: Suggestion['type']) => {
    switch (type) {
      case 'merge': return <GitMerge className="w-4 h-4 text-accent-purple" />
      case 'outdated': return <AlertTriangle className="w-4 h-4 text-yellow-500" />
      case 'update': return <Sparkles className="w-4 h-4 text-accent-green" />
    }
  }
  
  const getTypeColor = (type: Suggestion['type']) => {
    switch (type) {
      case 'merge': return 'border-accent-purple/30'
      case 'outdated': return 'border-yellow-500/30'
      case 'update': return 'border-accent-green/30'
    }
  }

  return (
    <div className="p-4">
      <div className="flex flex-col gap-3 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-gray-400">
            <Lightbulb className="w-4 h-4" />
            <span className="text-sm font-medium">Maintenance Insights</span>
          </div>
        </div>
        
        {onTrigger && projectId && (
          <div className="space-y-2">
            <textarea
              value={customMessage}
              onChange={(e) => setCustomMessage(e.target.value)}
              placeholder="Optional: Describe what you want the analysis to focus on..."
              className="w-full px-3 py-2 bg-dark-surface border border-dark-border rounded text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-accent-purple"
              rows={2}
              disabled={isTriggering || isProcessing || !!processingId}
            />
            <button
              onClick={handleTrigger}
              disabled={isTriggering || isProcessing || !!processingId}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-accent-purple text-white text-sm rounded hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title="Run full maintenance analysis"
            >
              <RefreshCw className={`w-4 h-4 ${isTriggering ? 'animate-spin' : ''}`} />
              {isTriggering ? 'Analyzing...' : 'Run Analysis'}
            </button>
          </div>
        )}
      </div>
      
      <div className="space-y-3">
        {suggestions.map(suggestion => (
          <div 
            key={suggestion.id} 
            className={`bg-dark-surface rounded-lg p-4 border-l-2 ${getTypeColor(suggestion.type)} 
              hover:bg-dark-hover transition-colors`}
          >
            <div className="flex items-start gap-3">
              {getTypeIcon(suggestion.type)}
              
              <div className="flex-1">
                <h4 className="text-sm font-medium text-white mb-1">{suggestion.title}</h4>
                <p className="text-xs text-gray-400 mb-2">{suggestion.description}</p>
                
                {suggestion.affectedFiles && (
                  <div className="mb-3">
                    <p className="text-xs text-gray-500 mb-1">Affected files:</p>
                    <div className="flex flex-wrap gap-1">
                      {suggestion.affectedFiles.map((file, idx) => (
                        <span 
                          key={idx}
                          className="text-xs bg-dark-bg px-2 py-0.5 rounded text-accent-blue hover:underline cursor-pointer"
                        >
                          {file}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="flex items-center gap-2">
                  <button 
                    onClick={() => handleAccept(suggestion.id)}
                    disabled={isProcessing || !!processingId}
                    className="flex items-center gap-1 px-3 py-1 bg-accent-blue text-white text-xs rounded hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {processingId === suggestion.id ? (
                      <>
                        <Loader2 className="w-3 h-3 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Check className="w-3 h-3" />
                        Accept
                      </>
                    )}
                  </button>
                  <button 
                    onClick={() => handleDismiss(suggestion.id)}
                    disabled={isProcessing || !!processingId}
                    className="flex items-center gap-1 px-3 py-1 bg-dark-border text-gray-300 text-xs rounded hover:bg-dark-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <X className="w-3 h-3" />
                    Dismiss
                  </button>
                </div>
                
                {/* Show execution result for this suggestion */}
                {executionResult && executionResult.suggestionId === suggestion.id && (
                  <div className={`mt-3 p-3 rounded text-xs ${
                    executionResult.success 
                      ? 'bg-green-900/20 border border-green-700/30 text-green-300'
                      : 'bg-red-900/20 border border-red-700/30 text-red-300'
                  }`}>
                    {executionResult.success ? (
                      <div>
                        <div className="font-semibold mb-1">✓ Changes Applied:</div>
                        <ul className="list-disc list-inside space-y-1">
                          {executionResult.changes?.map((change, idx) => (
                            <li key={idx}>{change}</li>
                          ))}
                        </ul>
                      </div>
                    ) : (
                      <div>
                        <div className="font-semibold mb-1">✗ Error:</div>
                        <div>{executionResult.error}</div>
                        <button
                          onClick={() => handleAccept(suggestion.id)}
                          className="mt-2 px-2 py-1 bg-red-700 text-white rounded hover:bg-red-600 text-xs"
                        >
                          Retry
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        
        {suggestions.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Lightbulb className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No suggestions</p>
            <p className="text-xs">Workspace looks well organized!</p>
          </div>
        )}
      </div>
    </div>
  )
}
