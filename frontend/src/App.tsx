import { useState, useEffect } from 'react'
import { ChatInterface } from './components/ChatInterface'
import { FileBrowser, FileItem } from './components/FileBrowser'
import { Timeline } from './components/Timeline'
import { Insights } from './components/Insights'
import { TopBar } from './components/TopBar'
import { NewProjectModal } from './components/NewProjectModal'
import { FileViewer } from './components/FileViewer'
import { SettingsModal } from './components/SettingsModal'
import { api } from './services/api'
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
  type: 'search' | 'read' | 'write' | 'execute'
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
  const [currentProject, setCurrentProject] = useState<Project | null>(null)
  const [projects, setProjects] = useState<Project[]>([])
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI workspace assistant. I can help you organize notes, search through your files, and maintain your knowledge base. Create or select a project to get started.',
      timestamp: new Date(),
      toolActivity: []
    }
  ])
  
  const [sidePanel, setSidePanel] = useState<SidePanel>('files')
  const [showSidePanel, setShowSidePanel] = useState(true)
  const [showNewProjectModal, setShowNewProjectModal] = useState(false)
  const [showSettingsModal, setShowSettingsModal] = useState(false)
  const [workspaceHealth, setWorkspaceHealth] = useState<'good' | 'warning' | 'critical'>('good')
  const [isLoading, setIsLoading] = useState(false)
  
  // File viewer state
  const [viewingFile, setViewingFile] = useState<{
    path: string
    name: string
    content: string
  } | null>(null)
  const [fileLoading, setFileLoading] = useState(false)
  
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

  // Check backend health on mount
  useEffect(() => {
    checkHealth()
    loadProjects()
  }, [])

  const checkHealth = async () => {
    try {
      const health = await api.checkHealth()
      if (health.services.rust_core && health.services.main_agent) {
        setWorkspaceHealth('good')
      } else if (health.services.rust_core) {
        setWorkspaceHealth('warning')
      } else {
        setWorkspaceHealth('critical')
      }
    } catch {
      setWorkspaceHealth('critical')
    }
  }

  const loadProjects = async () => {
    try {
      const projectsData = await api.listProjects()
      const projectsList = projectsData.map(p => ({
        id: p.id,
        name: p.name,
        description: p.description,
        createdAt: new Date(p.created_at),
        lastAccessed: new Date(p.last_accessed)
      }))
      setProjects(projectsList)
      
      if (projectsList.length > 0) {
        // Auto-select the most recently accessed project
        const sorted = [...projectsList].sort((a, b) => 
          b.lastAccessed.getTime() - a.lastAccessed.getTime()
        )
        setCurrentProject(sorted[0])
      }
    } catch (err) {
      console.error('Failed to load projects:', err)
    }
  }

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    
    // Create a placeholder assistant message for streaming updates
    const assistantMessageId = (Date.now() + 1).toString()
    const placeholderMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      toolActivity: []
    }
    setMessages(prev => [...prev, placeholderMessage])
    
    try {
      // Prepare chat history (last 10 messages for context, excluding assistant messages without content)
      const chatHistory = messages
        .filter(m => m.role !== 'assistant' || m.content) // Keep all user messages and assistant messages with content
        .slice(-10) // Last 10 messages
        .map(m => ({
          role: m.role,
          content: m.content
        }))
      
      const request = {
        message: content,
        context: currentProject?.description,
        tools: ['search', 'read_file', 'write_file', 'list_directory', 'execute_command', 'find_recents', 'create_directory', 'delete_file'],
        project_id: currentProject?.id,
        chat_history: chatHistory
      }
      
      let streamedContent = ''
      const toolActivities: ToolActivity[] = []
      
      // Use streaming API
      await api.sendMessageStream(
        request,
        // onEvent - handle streaming events
        (event) => {
          if (event.type === 'status') {
            // Update loading message
            streamedContent = event.message || 'Processing...'
          } else if (event.type === 'iteration') {
            streamedContent += `\n[Iteration ${event.number}]`
          } else if (event.type === 'tool_call') {
            const activity: ToolActivity = {
              type: event.name as 'search' | 'read' | 'write' | 'execute',
              description: `${event.name}: ${JSON.stringify(event.arguments)}`,
              timestamp: new Date()
            }
            toolActivities.push(activity)
            streamedContent += `\n🔧 ${event.name}...`
          } else if (event.type === 'tool_result') {
            streamedContent += `\n✓ ${event.name ?? 'operation'} ${event.success ? 'completed' : 'failed'}`
          } else if (event.type === 'response') {
            streamedContent = event.content || ''
          }
          
          // Update the placeholder message with streamed content
          setMessages(prev => prev.map(m => 
            m.id === assistantMessageId 
              ? { ...m, content: streamedContent, toolActivity: toolActivities }
              : m
          ))
        },
        // onComplete - final response received
        (response) => {
          const finalMessage: Message = {
            id: response.message_id,
            role: 'assistant',
            content: response.response,
            timestamp: new Date(),
            toolActivity: response.tool_calls?.map(tc => ({
              type: tc.name as 'search' | 'read' | 'write' | 'execute',
              description: `${tc.name}: ${JSON.stringify(tc.arguments)}`,
              timestamp: new Date()
            }))
          }
          
          // Replace placeholder with final message
          setMessages(prev => prev.map(m => 
            m.id === assistantMessageId ? finalMessage : m
          ))
          
          // Check if we should trigger a summary (every 10 messages)
          const totalMessages = messages.length + 2
          if (totalMessages % 10 === 0 && currentProject) {
            triggerSummaryGeneration(currentProject.id, [...messages, userMessage, finalMessage])
          }
        },
        // onError - handle errors
        (error) => {
          console.error('Streaming error:', error)
          const errorMessage: Message = {
            id: assistantMessageId,
            role: 'assistant',
            content: `Sorry, I encountered an error: ${error.message}`,
            timestamp: new Date()
          }
          setMessages(prev => prev.map(m => 
            m.id === assistantMessageId ? errorMessage : m
          ))
        }
      )
    } catch (error) {
      console.error('Failed to send message:', error)
      const errorMessage: Message = {
        id: assistantMessageId,
        role: 'assistant',
        content: `Sorry, I encountered an error connecting to the backend service. Please make sure all services are running.\n\nError: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date()
      }
      setMessages(prev => prev.map(m => 
        m.id === assistantMessageId ? errorMessage : m
      ))
    } finally {
      setIsLoading(false)
    }
  }

  const triggerSummaryGeneration = async (projectId: string, messageHistory: Message[]) => {
    // This would call the maintenance agent to create a summary
    // For now, we'll just log that a summary should be created
    console.log('Summary should be generated for project:', projectId)
    console.log('Message count:', messageHistory.length)
    // TODO: Implement actual summary generation via maintenance agent
  }

  const handleCreateProject = async (name: string, description: string, location?: string) => {
    try {
      const project = await api.createProject(name, description, location)
      const newProject: Project = {
        id: project.id,
        name: project.name,
        description: project.description,
        createdAt: new Date(project.created_at),
        lastAccessed: new Date(project.last_accessed)
      }
      setProjects(prev => [...prev, newProject])
      setCurrentProject(newProject)
    } catch {
      // Fallback to local creation
      const newProject: Project = {
        id: Date.now().toString(),
        name,
        description,
        createdAt: new Date(),
        lastAccessed: new Date()
      }
      setProjects(prev => [...prev, newProject])
      setCurrentProject(newProject)
    }
    
    setShowNewProjectModal(false)
    setMessages([{
      id: '1',
      role: 'assistant',
      content: `Welcome to your new project "${name}"! I'm ready to help you organize and explore your workspace. What would you like to start with?`,
      timestamp: new Date()
    }])
  }

  const handleProjectChange = (project: Project) => {
    setCurrentProject(project)
    // Reset chat when switching projects
    setMessages([{
      id: '1',
      role: 'assistant',
      content: `Switched to project "${project.name}". How can I help you today?`,
      timestamp: new Date()
    }])
  }

  const handleFileSelect = async (file: FileItem, fullPath: string) => {
    if (file.type !== 'file') return
    
    setFileLoading(true)
    try {
      const content = await api.getFileContent(currentProject?.id || '1', fullPath)
      setViewingFile({
        path: fullPath,
        name: file.name,
        content
      })
    } catch {
      // Show empty file viewer with mock content
      setViewingFile({
        path: fullPath,
        name: file.name,
        content: `# ${file.name}\n\nFile content would be loaded from the workspace.\n\nPath: ${fullPath}`
      })
    } finally {
      setFileLoading(false)
    }
  }

  const handleFileSave = async (content: string) => {
    if (!viewingFile || !currentProject) return
    
    try {
      await api.writeFile(currentProject.id, viewingFile.path, content)
      setViewingFile({ ...viewingFile, content })
    } catch (error) {
      console.error('Failed to save file:', error)
    }
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
        projects={projects}
        workspaceHealth={workspaceHealth}
        onNewProject={() => setShowNewProjectModal(true)}
        onProjectChange={handleProjectChange}
        onSettingsClick={() => setShowSettingsModal(true)}
        suggestionCount={suggestions.length}
      />
      
      <div className="flex-1 flex overflow-hidden">
        {/* Main Chat Area */}
        <div className={`flex-1 flex flex-col ${showSidePanel || viewingFile ? 'max-w-[45%]' : ''}`}>
          <ChatInterface 
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
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
          <div className="w-[30%] border-l border-dark-border flex flex-col">
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
              {sidePanel === 'files' && (
                <FileBrowser 
                  projectId={currentProject?.id}
                  onFileSelect={handleFileSelect}
                />
              )}
              {sidePanel === 'timeline' && <Timeline entries={timeline} />}
              {sidePanel === 'insights' && <Insights suggestions={suggestions} />}
            </div>
          </div>
        )}
        
        {/* File Preview Panel */}
        {viewingFile && (
          <div className="w-[25%]">
            <FileViewer
              filePath={viewingFile.path}
              fileName={viewingFile.name}
              content={viewingFile.content}
              isLoading={fileLoading}
              onClose={() => setViewingFile(null)}
              onSave={handleFileSave}
              asSidePanel={true}
            />
          </div>
        )}
      </div>
      
      {showNewProjectModal && (
        <NewProjectModal 
          onClose={() => setShowNewProjectModal(false)}
          onCreate={handleCreateProject}
        />
      )}
      
      {showSettingsModal && (
        <SettingsModal
          onClose={() => setShowSettingsModal(false)}
        />
      )}
    </div>
  )
}

export default App
