import { useState } from 'react'
import { 
  ChevronDown, 
  Settings, 
  Plus,
  Circle,
  Bell
} from 'lucide-react'
import type { Project } from '../App'

type Props = {
  project: Project | null
  projects: Project[]
  workspaceHealth: 'good' | 'warning' | 'critical'
  onNewProject: () => void
  onProjectChange: (project: Project) => void
  onSettingsClick?: () => void
  suggestionCount: number
}

export function TopBar({ project, projects, workspaceHealth, onNewProject, onProjectChange, suggestionCount, onSettingsClick }: Props) {
  const [showProjectDropdown, setShowProjectDropdown] = useState(false)
  
  const getHealthColor = () => {
    switch (workspaceHealth) {
      case 'good': return 'text-green-400'
      case 'warning': return 'text-yellow-400'
      case 'critical': return 'text-red-400'
    }
  }
  
  const getHealthLabel = () => {
    switch (workspaceHealth) {
      case 'good': return 'Workspace healthy'
      case 'warning': return 'Needs attention'
      case 'critical': return 'Issues detected'
    }
  }

  return (
    <header className="h-14 bg-[#2a2a2a] border-b border-[rgba(255,255,255,0.06)] flex items-center justify-between px-6 flex-shrink-0">
      <div className="flex items-center gap-6">
        {/* Logo */}
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center shadow-lg">
            <span className="text-white text-sm font-bold">A</span>
          </div>
          <span className="font-semibold text-white text-[15px]">Agent Workspace</span>
        </div>
        
        {/* Project Selector */}
        <div className="flex items-center gap-2 relative">
          <button 
            onClick={() => setShowProjectDropdown(!showProjectDropdown)}
            className="flex items-center gap-2.5 px-4 py-2 bg-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.08)] border border-[rgba(255,255,255,0.08)] 
              hover:border-[rgba(255,255,255,0.12)] rounded-lg transition-all">

            <span className="text-sm text-white font-medium">{project?.name || 'Select Project'}</span>
            <ChevronDown className="w-4 h-4 text-white/50" />
          </button>
          
          {/* Dropdown Menu */}
          {showProjectDropdown && (
            <>
              <div 
                className="fixed inset-0 z-10" 
                onClick={() => setShowProjectDropdown(false)}
              />
              <div className="absolute top-full left-0 mt-2 bg-[#2a2a2a] border border-[rgba(255,255,255,0.08)] rounded-xl 
                shadow-2xl z-20 min-w-[220px] max-h-[400px] overflow-y-auto">
                {projects.length > 0 ? (
                  projects.map(p => (
                    <button
                      key={p.id}
                      onClick={() => {
                        onProjectChange(p)
                        setShowProjectDropdown(false)
                      }}
                      className={`w-full text-left px-4 py-3 hover:bg-[rgba(255,255,255,0.08)] transition-all first:rounded-t-xl 
                        last:rounded-b-xl border-b border-[rgba(255,255,255,0.04)] last:border-b-0
                        ${p.id === project?.id ? 'bg-[rgba(255,255,255,0.06)] text-blue-400' : 'text-white'}`}>

                      <div className="font-medium text-[14px]">{p.name}</div>
                      {p.description && (
                        <div className="text-xs text-white/50 truncate mt-0.5">{p.description}</div>
                      )}
                    </button>
                  ))
                ) : (
                  <div className="px-4 py-3 text-white/50 text-sm">
                    No projects yet
                  </div>
                )}
              </div>
            </>
          )}
          
          <button 
            onClick={onNewProject}
            className="w-9 h-9 flex items-center justify-center text-white/50 hover:text-white 
              hover:bg-[rgba(255,255,255,0.08)] border border-[rgba(255,255,255,0.08)] hover:border-[rgba(255,255,255,0.12)] rounded-lg transition-all"
            title="New Project"
          >
            <Plus className="w-[18px] h-[18px]" />
          </button>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button className="relative w-9 h-9 flex items-center justify-center text-white/50 hover:text-white 
          hover:bg-white/8 rounded-lg transition-all">
          <Bell className="w-[18px] h-[18px]" />
          {suggestionCount > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-blue-500 text-white text-[10px] font-semibold 
              rounded-full flex items-center justify-center">
              {suggestionCount}
            </span>
          )}
        </button>
        
        {/* Workspace Health */}
        <div className="flex items-center gap-2.5 px-3 py-2 rounded-lg hover:bg-white/8 transition-all cursor-pointer" 
          title={getHealthLabel()}>
          <Circle className={`w-2 h-2 fill-current ${getHealthColor()}`} />
          <span className="text-xs text-white/60 font-medium">Workspace</span>
        </div>
        
        {/* Settings */}
        <button 
          onClick={onSettingsClick}
          className="w-9 h-9 flex items-center justify-center text-white/50 hover:text-white 
            hover:bg-white/8 rounded-lg transition-all"
        >
          <Settings className="w-[18px] h-[18px]" />
        </button>
      </div>
    </header>
  )
}
