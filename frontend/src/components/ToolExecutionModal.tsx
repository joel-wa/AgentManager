import { useState, useEffect } from 'react'
import { X, Play, Loader } from 'lucide-react'
import { api } from '../services/api'

interface ToolParam {
  name: string
  type: string
  description?: string
  required?: boolean
}

interface Tool {
  name: string
  description: string
  parameters: ToolParam[]
}

type Props = {
  isOpen: boolean
  onClose: () => void
  projectId?: string
}

// Define available tools with their parameters
const AVAILABLE_TOOLS: Tool[] = [
  {
    name: 'search',
    description: 'Search for files containing specific text',
    parameters: [
      { name: 'query', type: 'string', description: 'Text to search for', required: true },
      { name: 'path', type: 'string', description: 'Optional path to search in', required: false }
    ]
  },
  {
    name: 'read_file',
    description: 'Read the contents of a file',
    parameters: [
      { name: 'file_path', type: 'string', description: 'Path to the file', required: true }
    ]
  },
  {
    name: 'write_file',
    description: 'Write content to a file',
    parameters: [
      { name: 'file_path', type: 'string', description: 'Path to the file', required: true },
      { name: 'content', type: 'string', description: 'Content to write', required: true }
    ]
  },
  {
    name: 'list_directory',
    description: 'List files in a directory',
    parameters: [
      { name: 'path', type: 'string', description: 'Directory path (default: current directory)', required: false }
    ]
  },
  {
    name: 'execute_command',
    description: 'Execute a shell command',
    parameters: [
      { name: 'command', type: 'string', description: 'Command to execute', required: true }
    ]
  },
  {
    name: 'create_directory',
    description: 'Create a new directory',
    parameters: [
      { name: 'path', type: 'string', description: 'Path for the new directory', required: true }
    ]
  },
  {
    name: 'delete_file',
    description: 'Delete a file',
    parameters: [
      { name: 'file_path', type: 'string', description: 'Path to the file to delete', required: true }
    ]
  }
]

export function ToolExecutionModal({ isOpen, onClose, projectId }: Props) {
  const [selectedTool, setSelectedTool] = useState<Tool | null>(null)
  const [parameters, setParameters] = useState<Record<string, string>>({})
  const [isExecuting, setIsExecuting] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen) {
      setSelectedTool(null)
      setParameters({})
      setResult(null)
      setError(null)
    }
  }, [isOpen])

  const handleToolSelect = (tool: Tool) => {
    setSelectedTool(tool)
    setParameters({})
    setResult(null)
    setError(null)
  }

  const handleParameterChange = (paramName: string, value: string) => {
    setParameters(prev => ({
      ...prev,
      [paramName]: value
    }))
  }

  const handleExecute = async () => {
    if (!selectedTool || !projectId) return

    // Validate required parameters
    const missingParams = selectedTool.parameters
      .filter(p => p.required && !parameters[p.name]?.trim())
      .map(p => p.name)

    if (missingParams.length > 0) {
      setError(`Missing required parameters: ${missingParams.join(', ')}`)
      return
    }

    setIsExecuting(true)
    setError(null)

    try {
      // Send a message to the agent to execute the tool
      const message = `Execute tool: ${selectedTool.name} with parameters: ${JSON.stringify(parameters, null, 2)}`
      
      const response = await api.sendMessage({
        message,
        tools: [selectedTool.name],
        project_id: projectId,
        context: `Manual tool execution: ${selectedTool.name}`
      })

      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute tool')
    } finally {
      setIsExecuting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div
      className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose()
        }
      }}
    >
      <div className="bg-[#2a2a2a] border border-[rgba(255,255,255,0.12)] rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[rgba(255,255,255,0.08)]">
          <div>
            <h2 className="text-lg font-semibold text-white">Manual Tool Execution</h2>
            <p className="text-sm text-white/50 mt-0.5">Execute tools directly with custom parameters</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center text-white/50 hover:text-white/90 hover:bg-white/8 rounded-lg transition-all"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selectedTool ? (
            // Tool Selection
            <div>
              <h3 className="text-sm font-semibold text-white/70 mb-3">Select a Tool</h3>
              <div className="space-y-2">
                {AVAILABLE_TOOLS.map(tool => (
                  <button
                    key={tool.name}
                    onClick={() => handleToolSelect(tool)}
                    className="w-full text-left px-4 py-3 bg-[rgba(255,255,255,0.04)] hover:bg-[rgba(255,255,255,0.08)] 
                      border border-[rgba(255,255,255,0.08)] rounded-xl transition-colors"
                  >
                    <div className="font-mono text-sm text-blue-400 mb-1">{tool.name}</div>
                    <div className="text-xs text-white/60">{tool.description}</div>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            // Tool Execution Form
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-mono text-lg text-blue-400">{selectedTool.name}</h3>
                  <p className="text-sm text-white/60 mt-1">{selectedTool.description}</p>
                </div>
                <button
                  onClick={() => setSelectedTool(null)}
                  className="px-3 py-1.5 text-sm text-white/60 hover:text-white hover:bg-white/8 rounded-lg transition-colors"
                >
                  Change Tool
                </button>
              </div>

              {/* Parameters Form */}
              <div className="space-y-4 mb-6">
                {selectedTool.parameters.map(param => (
                  <div key={param.name}>
                    <label className="block text-sm text-white/70 mb-1.5">
                      {param.name}
                      {param.required && <span className="text-red-400 ml-1">*</span>}
                    </label>
                    {param.description && (
                      <p className="text-xs text-white/40 mb-2">{param.description}</p>
                    )}
                    {param.type === 'string' && param.name === 'content' ? (
                      <textarea
                        value={parameters[param.name] || ''}
                        onChange={(e) => handleParameterChange(param.name, e.target.value)}
                        placeholder={`Enter ${param.name}...`}
                        rows={6}
                        className="w-full px-3 py-2 bg-[rgba(0,0,0,0.3)] border border-[rgba(255,255,255,0.1)] 
                          rounded-lg text-white text-sm outline-none focus:border-blue-500 font-mono resize-none"
                      />
                    ) : (
                      <input
                        type="text"
                        value={parameters[param.name] || ''}
                        onChange={(e) => handleParameterChange(param.name, e.target.value)}
                        placeholder={`Enter ${param.name}...`}
                        className="w-full px-3 py-2 bg-[rgba(0,0,0,0.3)] border border-[rgba(255,255,255,0.1)] 
                          rounded-lg text-white text-sm outline-none focus:border-blue-500 font-mono"
                      />
                    )}
                  </div>
                ))}
              </div>

              {/* Execute Button */}
              <button
                onClick={handleExecute}
                disabled={isExecuting}
                className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-500 hover:bg-blue-600 
                  disabled:bg-blue-500/30 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
              >
                {isExecuting ? (
                  <>
                    <Loader className="w-4 h-4 animate-spin" />
                    Executing...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4" />
                    Execute Tool
                  </>
                )}
              </button>

              {/* Error Display */}
              {error && (
                <div className="mt-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg">
                  <div className="text-sm text-red-400">{error}</div>
                </div>
              )}

              {/* Result Display */}
              {result && (
                <div className="mt-4">
                  <h4 className="text-sm font-semibold text-white/70 mb-2">Result</h4>
                  <div className="p-4 bg-[rgba(0,0,0,0.3)] border border-[rgba(255,255,255,0.1)] rounded-lg">
                    <pre className="text-sm text-white/90 whitespace-pre-wrap font-mono overflow-auto max-h-96">
                      {JSON.stringify(result, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[rgba(255,255,255,0.08)] bg-[rgba(0,0,0,0.2)]">
          <div className="flex items-center justify-between text-xs text-white/40">
            <span>Tool execution uses the same agent that powers the chat</span>
            <button
              onClick={onClose}
              className="px-3 py-1.5 hover:bg-white/8 rounded text-white/60 hover:text-white transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
