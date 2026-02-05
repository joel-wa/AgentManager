import { X, Plus } from 'lucide-react'
import { useState } from 'react'

export type ChatTab = {
  id: string
  projectId: string
  projectName: string
  title: string
  timestamp: Date
}

type Props = {
  tabs: ChatTab[]
  activeTabId: string
  onTabChange: (tabId: string) => void
  onTabClose: (tabId: string) => void
  onNewTab: () => void
}

export function ChatTabs({ tabs, activeTabId, onTabChange, onTabClose, onNewTab }: Props) {
  const [hoveredTabId, setHoveredTabId] = useState<string | null>(null)

  const handleTabClose = (e: React.MouseEvent, tabId: string) => {
    e.stopPropagation()
    onTabClose(tabId)
  }

  return (
    <div className="flex items-center gap-1 bg-[#2a2a2a] border-b border-[rgba(255,255,255,0.06)] px-2 py-1 overflow-x-auto">
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => onTabChange(tab.id)}
          onMouseEnter={() => setHoveredTabId(tab.id)}
          onMouseLeave={() => setHoveredTabId(null)}
          className={`
            group relative flex items-center gap-2 px-3 py-2 rounded-t-lg transition-all min-w-[120px] max-w-[200px]
            ${activeTabId === tab.id 
              ? 'bg-[#1e1e1e] text-white border-t-2 border-blue-500' 
              : 'bg-[#2a2a2a] text-white/60 hover:bg-white/4 hover:text-white'
            }
          `}
        >
          <div className="flex-1 truncate text-sm text-left">
            <div className="font-medium truncate">{tab.title}</div>
            <div className="text-xs text-white/40 truncate">{tab.projectName}</div>
          </div>
          
          {(hoveredTabId === tab.id || tabs.length > 1) && (
            <button
              onClick={(e) => handleTabClose(e, tab.id)}
              className="flex-shrink-0 p-0.5 rounded hover:bg-white/10 transition-colors"
              title="Close tab"
            >
              <X className="w-3 h-3" />
            </button>
          )}
        </button>
      ))}
      
      <button
        onClick={onNewTab}
        className="flex items-center justify-center w-8 h-8 rounded-lg text-white/50 hover:text-white hover:bg-white/8 transition-all"
        title="New chat tab"
      >
        <Plus className="w-4 h-4" />
      </button>
    </div>
  )
}
