import { useState, useEffect } from 'react'
import { X, FolderOpen, Globe, Bot, Palette, Save, RefreshCw } from 'lucide-react'
import { api, Settings } from '../services/api'

type Props = {
  onClose: () => void
  onSettingsChange?: (settings: Settings) => void
}

type ServiceStatusState = {
  rust_core: boolean
  agent: boolean
  maintenance: boolean
}

export function SettingsModal({ onClose, onSettingsChange }: Props) {
  const [settings, setSettings] = useState<Settings>({
    workspace_root: '',
    ollama_url: 'http://localhost:11434',
    ollama_model: 'gemma:7b',
    theme: 'dark',
  })
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [serviceStatus, setServiceStatus] = useState<ServiceStatusState>({
    rust_core: false,
    agent: false,
    maintenance: false,
  })

  useEffect(() => {
    loadSettings()
    checkServices()
  }, [])

  const loadSettings = async () => {
    setIsLoading(true)
    try {
      const loadedSettings = await api.getSettings()
      setSettings(loadedSettings)
    } catch (error) {
      console.error('Failed to load settings:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const checkServices = async () => {
    const status = await api.checkHealth()
    setServiceStatus({
      rust_core: status.services.rust_core,
      agent: status.services.main_agent,
      maintenance: status.services.maintenance_agent
    })
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      const updated = await api.updateSettings(settings)
      setSettings(updated)
      onSettingsChange?.(updated)
    } catch (error) {
      console.error('Failed to save settings:', error)
    } finally {
      setIsSaving(false)
    }
  }

  const handleChange = (key: keyof Settings, value: string) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-dark-surface rounded-xl shadow-2xl w-full max-w-2xl mx-4 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-dark-border">
          <h2 className="text-lg font-semibold text-white">Settings</h2>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white hover:bg-dark-hover rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center p-12">
            <div className="animate-spin w-8 h-8 border-2 border-accent-blue border-t-transparent rounded-full" />
          </div>
        ) : (
          <div className="p-4 space-y-6">
            {/* Workspace Root */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
                <FolderOpen className="w-4 h-4 text-accent-orange" />
                Workspace Root Directory
              </label>
              <p className="text-xs text-gray-500">
                The main folder where all your projects and files will be stored
              </p>
              <input
                type="text"
                value={settings.workspace_root}
                onChange={(e) => handleChange('workspace_root', e.target.value)}
                placeholder="e.g., C:\Users\YourName\.agent-workspace"
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-4 py-2.5
                  text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue transition-colors"
              />
            </div>

            {/* Ollama Settings */}
            <div className="space-y-4">
              <h3 className="flex items-center gap-2 text-sm font-medium text-gray-300">
                <Bot className="w-4 h-4 text-accent-green" />
                AI Model Configuration
              </h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs text-gray-400">Ollama URL</label>
                  <input
                    type="text"
                    value={settings.ollama_url}
                    onChange={(e) => handleChange('ollama_url', e.target.value)}
                    placeholder="http://localhost:11434"
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2
                      text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue"
                  />
                </div>
                
                <div className="space-y-2">
                  <label className="text-xs text-gray-400">Model</label>
                  <input
                    type="text"
                    value={settings.ollama_model}
                    onChange={(e) => handleChange('ollama_model', e.target.value)}
                    placeholder="gemma:7b"
                    className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2
                      text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent-blue"
                  />
                </div>
              </div>
            </div>

            {/* Theme */}
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
                <Palette className="w-4 h-4 text-accent-purple" />
                Theme
              </label>
              <select
                value={settings.theme}
                onChange={(e) => handleChange('theme', e.target.value)}
                className="w-full bg-dark-bg border border-dark-border rounded-lg px-3 py-2.5
                  text-white focus:outline-none focus:border-accent-blue cursor-pointer"
              >
                <option value="dark">Dark</option>
                <option value="light">Light</option>
              </select>
            </div>

            {/* Service Status */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
                  <Globe className="w-4 h-4 text-accent-blue" />
                  Service Status
                </label>
                <button
                  onClick={checkServices}
                  className="p-1 text-gray-400 hover:text-white transition-colors"
                  title="Refresh status"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
              
              <div className="grid grid-cols-3 gap-2">
                <div className={`p-3 rounded-lg border ${
                  serviceStatus.rust_core 
                    ? 'border-green-500/30 bg-green-500/10' 
                    : 'border-red-500/30 bg-red-500/10'
                }`}>
                  <div className="text-xs text-gray-400">Rust Core</div>
                  <div className={`text-sm font-medium ${
                    serviceStatus.rust_core ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {serviceStatus.rust_core ? 'Online' : 'Offline'}
                  </div>
                </div>
                
                <div className={`p-3 rounded-lg border ${
                  serviceStatus.agent 
                    ? 'border-green-500/30 bg-green-500/10' 
                    : 'border-red-500/30 bg-red-500/10'
                }`}>
                  <div className="text-xs text-gray-400">Agent</div>
                  <div className={`text-sm font-medium ${
                    serviceStatus.agent ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {serviceStatus.agent ? 'Online' : 'Offline'}
                  </div>
                </div>
                
                <div className={`p-3 rounded-lg border ${
                  serviceStatus.maintenance 
                    ? 'border-green-500/30 bg-green-500/10' 
                    : 'border-red-500/30 bg-red-500/10'
                }`}>
                  <div className="text-xs text-gray-400">Maintenance</div>
                  <div className={`text-sm font-medium ${
                    serviceStatus.maintenance ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {serviceStatus.maintenance ? 'Online' : 'Offline'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-4 border-t border-dark-border">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-dark-hover text-gray-300 rounded-lg hover:bg-dark-border transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2 px-4 py-2 bg-accent-blue text-white rounded-lg hover:bg-blue-600 
              disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <Save className="w-4 h-4" />
            {isSaving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}
