import { Lightbulb, AlertTriangle, Sparkles, GitMerge, Check, X } from 'lucide-react'
import type { Suggestion } from '../App'

type Props = {
  suggestions: Suggestion[]
}

export function Insights({ suggestions }: Props) {
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
      <div className="flex items-center gap-2 mb-4 text-gray-400">
        <Lightbulb className="w-4 h-4" />
        <span className="text-sm font-medium">Maintenance Insights</span>
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
                  <button className="flex items-center gap-1 px-3 py-1 bg-accent-blue text-white text-xs rounded hover:bg-blue-600 transition-colors">
                    <Check className="w-3 h-3" />
                    Accept
                  </button>
                  <button className="flex items-center gap-1 px-3 py-1 bg-dark-border text-gray-300 text-xs rounded hover:bg-dark-hover transition-colors">
                    <X className="w-3 h-3" />
                    Dismiss
                  </button>
                </div>
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
