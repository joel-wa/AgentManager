import { useState, useEffect } from 'react'
import { Plus, Edit, Trash2, Save, X } from 'lucide-react'
import { api } from '../services/api'

interface Prompt {
  id: string
  name: string
  content: string
  createdAt: Date
  updatedAt: Date
}

type Props = {
  projectId?: string
}

export function Prompts({ projectId }: Props) {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [isCreating, setIsCreating] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editContent, setEditContent] = useState('')

  useEffect(() => {
    loadPrompts()
  }, [projectId])

  const loadPrompts = async () => {
    if (!projectId) return
    
    try {
      const data = await api.listPrompts(projectId)
      setPrompts(data)
    } catch (err) {
      console.error('Failed to load prompts:', err)
    }
  }

  const handleCreate = async () => {
    if (!projectId || !editName.trim() || !editContent.trim()) return
    
    try {
      await api.createPrompt(projectId, editName.trim(), editContent.trim())
      await loadPrompts()
      setIsCreating(false)
      setEditName('')
      setEditContent('')
    } catch (err) {
      console.error('Failed to create prompt:', err)
    }
  }

  const handleUpdate = async (promptId: string) => {
    if (!projectId || !editName.trim() || !editContent.trim()) return
    
    try {
      await api.updatePrompt(projectId, promptId, editName.trim(), editContent.trim())
      await loadPrompts()
      setEditingId(null)
      setEditName('')
      setEditContent('')
    } catch (err) {
      console.error('Failed to update prompt:', err)
    }
  }

  const handleDelete = async (promptId: string) => {
    if (!projectId) return
    if (!confirm('Are you sure you want to delete this prompt?')) return
    
    try {
      await api.deletePrompt(projectId, promptId)
      await loadPrompts()
    } catch (err) {
      console.error('Failed to delete prompt:', err)
    }
  }

  const startEdit = (prompt: Prompt) => {
    setEditingId(prompt.id)
    setEditName(prompt.name)
    setEditContent(prompt.content)
  }

  const cancelEdit = () => {
    setEditingId(null)
    setIsCreating(false)
    setEditName('')
    setEditContent('')
  }

  if (!projectId) {
    return (
      <div className="p-6 text-center text-white/40">
        Select a project to manage prompts
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col bg-[#2a2a2a]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-[rgba(255,255,255,0.06)]">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white">Quick Prompts</h2>
            <p className="text-sm text-white/50 mt-1">
              Create reusable prompts to insert with # syntax
            </p>
          </div>
          {!isCreating && !editingId && (
            <button
              onClick={() => setIsCreating(true)}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Prompt
            </button>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* Create Form */}
        {isCreating && (
          <div className="mb-4 p-4 bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] rounded-xl">
            <h3 className="text-sm font-semibold text-white mb-3">Create New Prompt</h3>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-white/60 mb-1">Prompt Name</label>
                <input
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="e.g., code-review, bug-fix, explain"
                  className="w-full px-3 py-2 bg-[rgba(0,0,0,0.3)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white text-sm outline-none focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-xs text-white/60 mb-1">Prompt Content</label>
                <textarea
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  placeholder="Enter the prompt text that will be inserted..."
                  rows={4}
                  className="w-full px-3 py-2 bg-[rgba(0,0,0,0.3)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white text-sm outline-none focus:border-blue-500 resize-none"
                />
              </div>
              
              <div className="flex gap-2">
                <button
                  onClick={handleCreate}
                  disabled={!editName.trim() || !editContent.trim()}
                  className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/30 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
                >
                  <Save className="w-3.5 h-3.5" />
                  Create
                </button>
                <button
                  onClick={cancelEdit}
                  className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/15 text-white text-sm rounded-lg transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Prompts List */}
        {prompts.length === 0 && !isCreating ? (
          <div className="text-center py-12">
            <div className="text-white/40 mb-4">No prompts yet</div>
            <button
              onClick={() => setIsCreating(true)}
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Your First Prompt
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            {prompts.map((prompt) => (
              <div
                key={prompt.id}
                className="p-4 bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.08)] rounded-xl hover:bg-[rgba(255,255,255,0.06)] transition-colors"
              >
                {editingId === prompt.id ? (
                  // Edit Mode
                  <div className="space-y-3">
                    <div>
                      <label className="block text-xs text-white/60 mb-1">Prompt Name</label>
                      <input
                        type="text"
                        value={editName}
                        onChange={(e) => setEditName(e.target.value)}
                        className="w-full px-3 py-2 bg-[rgba(0,0,0,0.3)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white text-sm outline-none focus:border-blue-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-xs text-white/60 mb-1">Prompt Content</label>
                      <textarea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        rows={4}
                        className="w-full px-3 py-2 bg-[rgba(0,0,0,0.3)] border border-[rgba(255,255,255,0.1)] rounded-lg text-white text-sm outline-none focus:border-blue-500 resize-none"
                      />
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleUpdate(prompt.id)}
                        disabled={!editName.trim() || !editContent.trim()}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 hover:bg-blue-600 disabled:bg-blue-500/30 disabled:cursor-not-allowed text-white text-sm rounded-lg transition-colors"
                      >
                        <Save className="w-3.5 h-3.5" />
                        Save
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="flex items-center gap-2 px-3 py-1.5 bg-white/10 hover:bg-white/15 text-white text-sm rounded-lg transition-colors"
                      >
                        <X className="w-3.5 h-3.5" />
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : (
                  // View Mode
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <div className="font-mono text-sm text-blue-400">#{prompt.name}</div>
                        <div className="text-xs text-white/40 mt-0.5">
                          Updated {prompt.updatedAt.toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex gap-1">
                        <button
                          onClick={() => startEdit(prompt)}
                          className="p-1.5 hover:bg-white/10 rounded text-white/60 hover:text-white transition-colors"
                          title="Edit"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(prompt.id)}
                          className="p-1.5 hover:bg-red-500/20 rounded text-white/60 hover:text-red-400 transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    <div className="text-sm text-white/70 whitespace-pre-wrap bg-[rgba(0,0,0,0.3)] p-3 rounded-lg border border-[rgba(255,255,255,0.05)]">
                      {prompt.content}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
