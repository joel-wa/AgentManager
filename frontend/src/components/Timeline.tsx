import { Clock, FileText, PenTool } from 'lucide-react'
import type { TimelineEntry } from '../App'

type Props = {
  entries: TimelineEntry[]
}

export function Timeline({ entries }: Props) {
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'read': return <FileText className="w-3 h-3 text-accent-green" />
      case 'write': return <PenTool className="w-3 h-3 text-accent-orange" />
      default: return <FileText className="w-3 h-3 text-gray-400" />
    }
  }

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-4 text-gray-400">
        <Clock className="w-4 h-4" />
        <span className="text-sm font-medium">Session Timeline</span>
      </div>
      
      <div className="space-y-4">
        {entries.map(entry => (
          <div key={entry.id} className="relative pl-6 border-l border-dark-border">
            <div className="absolute left-0 top-0 w-3 h-3 -translate-x-1.5 bg-dark-bg border-2 border-accent-blue rounded-full" />
            
            <div className="bg-dark-surface rounded-lg p-3 hover:bg-dark-hover transition-colors cursor-pointer">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-white">{entry.title}</span>
                <span className="text-xs text-gray-500">{formatTime(entry.timestamp)}</span>
              </div>
              
              <div className="space-y-1">
                {entry.files.map((file, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-sm text-gray-400">
                    {getActionIcon(file.action)}
                    <span className="capitalize text-xs text-gray-500">{file.action}:</span>
                    <span className="text-accent-blue hover:underline cursor-pointer">{file.path}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ))}
        
        {entries.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <Clock className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">No activity yet</p>
            <p className="text-xs">Your session history will appear here</p>
          </div>
        )}
      </div>
    </div>
  )
}
