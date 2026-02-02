import { useState } from 'react'
import { X, FolderPlus, Folder } from 'lucide-react'

type Props = {
  onClose: () => void
  onCreate: (name: string, description: string, location?: string) => void
}

export function NewProjectModal({ onClose, onCreate }: Props) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [customLocation, setCustomLocation] = useState('')
  const [useCustomLocation, setUseCustomLocation] = useState(false)
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (name.trim()) {
      onCreate(name.trim(), description.trim(), useCustomLocation ? customLocation.trim() : undefined)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-dark-surface rounded-xl shadow-2xl w-full max-w-md mx-4 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-border">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-accent-blue/20 rounded-lg flex items-center justify-center">
              <FolderPlus className="w-5 h-5 text-accent-blue" />
            </div>
            <h2 className="text-lg font-semibold text-white">New Project</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Form */}
        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Project Name
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="My Research Project"
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2.5
                text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue transition-colors"
              autoFocus
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Description <span className="text-gray-500">(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Brief description of your project..."
              rows={3}
              className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2.5
                text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue transition-colors resize-none"
            />
          </div>
          
          <div>
            <label className="flex items-center gap-2 text-sm font-medium text-gray-300 mb-2">
              <input
                type="checkbox"
                checked={useCustomLocation}
                onChange={e => setUseCustomLocation(e.target.checked)}
                className="w-4 h-4 bg-dark-bg border border-dark-border rounded focus:ring-accent-blue"
              />
              Custom Location <span className="text-gray-500">(optional)</span>
            </label>
            {useCustomLocation && (
              <div className="flex items-center gap-2">
                <Folder className="w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={customLocation}
                  onChange={e => setCustomLocation(e.target.value)}
                  placeholder="e.g., C:\Downloads\MyProject or ~/Downloads/MyProject"
                  className="flex-1 bg-dark-bg border border-dark-border rounded-lg px-4 py-2.5
                    text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue transition-colors"
                />
              </div>
            )}
            {!useCustomLocation && (
              <p className="text-xs text-gray-500 mt-1">
                Project will be created in the default workspace directory
              </p>
            )}
          </div>
          
          <div className="flex items-center gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2.5 bg-dark-hover text-gray-300 rounded-lg hover:bg-dark-border transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!name.trim()}
              className="flex-1 px-4 py-2.5 bg-accent-blue text-white rounded-lg hover:bg-blue-600 
                disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Create Project
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
