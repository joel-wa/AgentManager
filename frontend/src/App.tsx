import { useState } from 'react'
import { ChatInterface } from './components/ChatInterface'
import { FileBrowser } from './components/FileBrowser'
import { Timeline } from './components/Timeline'
import { Insights } from './components/Insights'
import { TopBar } from './components/TopBar'
import { NewProjectModal } from './components/NewProjectModal'
import { 
  FolderTree, 
  Clock, 
  Lightbulb,
  PanelRightClose,
  PanelRightOpen
} from 'lucide-react'

export type Project = {
  id: string
  name: string
  description?: string
  createdAt: Date
  lastAccessed: Date
}

export type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  toolActivity?: ToolActivity[]
}

export type ToolActivity = {
  type: 'search' | 'read' | 'write'
  description: string
  filePath?: string
  timestamp: Date
}

export type TimelineEntry = {
  id: string
  timestamp: Date
  title: string
  files: { action: string; path: string }[]
}

export type Suggestion = {
  id: string
  type: 'merge' | 'outdated' | 'update'
  title: string
  description: string
  affectedFiles?: string[]
}

type SidePanel = 'files' | 'search' | 'timeline' | 'insights'

function App() {
  const [currentProject, setCurrentProject] = useState<Project | null>({
    id: '1',
    name: 'ML Research Notes',
    description: 'Notes and research on machine learning topics',
    createdAt: new Date('2024-01-15'),
    lastAccessed: new Date()
  })
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI workspace assistant. I can help you organize notes, search through your files, and maintain your knowledge base. What would you like to work on today?',
      timestamp: new Date(),
      toolActivity: []
    }
  ])
  
  const [sidePanel, setSidePanel] = useState<SidePanel>('files')
  const [showSidePanel, setShowSidePanel] = useState(true)
  const [showNewProjectModal, setShowNewProjectModal] = useState(false)
  const [workspaceHealth] = useState<'good' | 'warning' | 'critical'>('good')
  
  const [suggestions] = useState<Suggestion[]>([
    {
      id: '1',
      type: 'merge',
      title: 'Consolidate similar files',
      description: 'Found 3 files with overlapping content about neural networks',
      affectedFiles: ['notes/nn_basics.md', 'research/neural_nets.md', 'drafts/nn_summary.md']
    },
    {
      id: '2',
      type: 'outdated',
      title: 'Outdated reference detected',
      description: 'api_v1_notes.md references deprecated API version',
      affectedFiles: ['api_v1_notes.md']
    }
  ])

  const [timeline] = useState<TimelineEntry[]>([
    {
      id: '1',
      timestamp: new Date(Date.now() - 3600000),
      title: 'Researched authentication patterns',
      files: [
        { action: 'read', path: 'strategy.md' },
        { action: 'write', path: 'oauth_notes.md' }
      ]
    },
    {
      id: '2',
      timestamp: new Date(Date.now() - 7200000),
      title: 'Implemented login flow',
      files: [
        { action: 'write', path: 'login_handler.py' }
      ]
    }
  ])

  const handleSendMessage = (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    
    // Simulate AI response with tool activity
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I\'ve searched through your workspace and found relevant information. Let me summarize the key points for you...\n\nBased on your notes, here are the main topics:\n\n1. **Authentication Patterns** - OAuth 2.0, JWT tokens\n2. **API Design** - RESTful principles, versioning strategies\n3. **Database Schema** - User models, session management',
        timestamp: new Date(),
        toolActivity: [
          { type: 'search', description: 'Searched workspace for relevant content', timestamp: new Date() },
          { type: 'read', description: 'Read auth/strategy.md', filePath: 'auth/strategy.md', timestamp: new Date() },
          { type: 'write', description: 'Created notes/session_summary.md', filePath: 'notes/session_summary.md', timestamp: new Date() }
        ]
      }
      setMessages(prev => [...prev, assistantMessage])
    }, 1500)
  }

  const handleCreateProject = (name: string, description: string) => {
    const newProject: Project = {
      id: Date.now().toString(),
      name,
      description,
      createdAt: new Date(),
      lastAccessed: new Date()
    }
    setCurrentProject(newProject)
    setShowNewProjectModal(false)
    setMessages([{
      id: '1',
      role: 'assistant',
      content: `Welcome to your new project "${name}"! I'm ready to help you organize and explore your workspace. What would you like to start with?`,
      timestamp: new Date()
    }])
  }

  const sidePanelTabs = [
    { id: 'files' as SidePanel, icon: FolderTree, label: 'Files' },
    { id: 'timeline' as SidePanel, icon: Clock, label: 'Timeline' },
    { id: 'insights' as SidePanel, icon: Lightbulb, label: 'Insights' }
  ]

  return (
    <div className="h-screen flex flex-col bg-dark-bg">
      <TopBar 
        project={currentProject}
        workspaceHealth={workspaceHealth}
        onNewProject={() => setShowNewProjectModal(true)}
        onProjectChange={setCurrentProject}
        suggestionCount={suggestions.length}
      />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Main Chat Area */}
        <div className={`flex-1 flex flex-col ${showSidePanel ? 'max-w-[60%]' : ''}`}>
          <ChatInterface 
            messages={messages}
            onSendMessage={handleSendMessage}
          />
        </div>
        
        {/* Side Panel Toggle */}
        <button
          onClick={() => setShowSidePanel(!showSidePanel)}
          className="p-2 hover:bg-dark-hover transition-colors self-start mt-2"
          title={showSidePanel ? 'Hide panel' : 'Show panel'}
        >
          {showSidePanel ? (
            <PanelRightClose className="w-5 h-5 text-gray-400" />
          ) : (
            <PanelRightOpen className="w-5 h-5 text-gray-400" />
          )}
        </button>
        
        {/* Side Panel */}
        {showSidePanel && (
          <div className="w-[40%] border-l border-dark-border flex flex-col">
            {/* Panel Tabs */}
            <div className="flex border-b border-dark-border">
              {sidePanelTabs.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setSidePanel(tab.id)}
                  className={`flex items-center gap-2 px-4 py-2 text-sm transition-colors
                    ${sidePanel === tab.id 
                      ? 'text-white border-b-2 border-accent-blue bg-dark-surface' 
                      : 'text-gray-400 hover:text-white hover:bg-dark-hover'
                    }`}
                >
                  <tab.icon className="w-4 h-4" />
                  {tab.label}
                  {tab.id === 'insights' && suggestions.length > 0 && (
                    <span className="bg-accent-blue text-white text-xs px-1.5 rounded-full">
                      {suggestions.length}
                    </span>
                  )}
                </button>
              ))}
            </div>
            
            {/* Panel Content */}
            <div className="flex-1 overflow-auto">
              {sidePanel === 'files' && <FileBrowser />}
              {sidePanel === 'timeline' && <Timeline entries={timeline} />}
              {sidePanel === 'insights' && <Insights suggestions={suggestions} />}
            </div>
          </div>
        )}
      </div>
      
      {showNewProjectModal && (
        <NewProjectModal 
          onClose={() => setShowNewProjectModal(false)}
          onCreate={handleCreateProject}
        />
      )}
    </div>
  )
}

export default App
