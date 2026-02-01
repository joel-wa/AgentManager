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
  workspaceHealth: 'good' | 'warning' | 'critical'
  onNewProject: () => void
  onProjectChange: (project: Project) => void
  suggestionCount: number
}

export function TopBar({ project, workspaceHealth, onNewProject, suggestionCount }: Props) {
  const getHealthColor = () => {
    switch (workspaceHealth) {
      case 'good': return 'text-green-500'
      case 'warning': return 'text-yellow-500'
      case 'critical': return 'text-red-500'
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
    <header className="h-12 bg-dark-surface border-b border-dark-border flex items-center justify-between px-4">
      <div className="flex items-center gap-4">
        {/* Logo */}
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 bg-gradient-to-br from-accent-blue to-accent-purple rounded-lg flex items-center justify-center">
            <span className="text-white text-xs font-bold">A</span>
          </div>
          <span className="font-semibold text-white">Agent Workspace</span>
        </div>
        
        {/* Project Selector */}
        <div className="flex items-center gap-2 ml-4">
          <button className="flex items-center gap-2 px-3 py-1.5 bg-dark-hover rounded-md hover:bg-dark-border transition-colors">
            <span className="text-sm text-white">{project?.name || 'Select Project'}</span>
            <ChevronDown className="w-4 h-4 text-gray-400" />
          </button>
          
          <button 
            onClick={onNewProject}
            className="p-1.5 text-gray-400 hover:text-white hover:bg-dark-hover rounded-md transition-colors"
            title="New Project"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        {/* Notifications */}
        <button className="relative p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors">
          <Bell className="w-5 h-5" />
          {suggestionCount > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 bg-accent-blue text-white text-[10px] rounded-full flex items-center justify-center">
              {suggestionCount}
            </span>
          )}
        </button>
        
        {/* Workspace Health */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md hover:bg-dark-hover transition-colors cursor-pointer" title={getHealthLabel()}>
          <Circle className={`w-2 h-2 fill-current ${getHealthColor()}`} />
          <span className="text-xs text-gray-400">Workspace</span>
        </div>
        
        {/* Settings */}
        <button className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors">
          <Settings className="w-5 h-5" />
        </button>
      </div>
    </header>
  )
}
