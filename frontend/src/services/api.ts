/**
 * API Service - Handles communication with Rust Core backend
 * All requests go through Rust Core (port 8000) which coordinates with Python services
 */

import type { Prompt, PromptData } from '../types/prompt'

const RUST_CORE_URL = 'http://localhost:8000';

export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  last_accessed: string;
}

export interface FileItem {
  name: string;
  type: 'file' | 'folder';
  extension?: string;
  children?: FileItem[];
  summary?: string;
  path?: string;
}

export interface ChatRequest {
  message: string;
  context?: string;
  tools: string[];
  project_id?: string;
  chat_history?: Array<{ role: string; content: string }>;
}

export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

export interface ChatResponse {
  response: string;
  tool_calls?: ToolCall[];
  message_id: string;
}

export interface StreamEvent {
  type: 'status' | 'iteration' | 'tool_call' | 'tool_result' | 'response' | 'done' | 'error';
  message?: string;
  number?: number;
  name?: string;
  arguments?: Record<string, unknown>;
  success?: boolean;
  preview?: string;
  content?: string;
  message_id?: string;
  tool_calls?: number;
}

export interface TimelineEntry {
  id: string;
  timestamp: string;
  title: string;
  files: { action: string; path: string }[];
}

export interface Suggestion {
  id: string;
  type: 'merge' | 'outdated' | 'update';
  title: string;
  description: string;
  affected_files?: string[];
}

export interface Settings {
  workspace_root: string;
  ollama_url: string;
  ollama_model: string;
  maintenance_model?: string;
  theme: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  services: {
    rust_core: boolean;
    main_agent: boolean;
    maintenance_agent: boolean;
    embeddings: boolean;
  };
}

export interface VersionMetadata {
  version: number;
  timestamp: string;
  file_size: number;
  content_hash: string;
  message?: string;
}

export interface VersionEntry {
  metadata: VersionMetadata;
  content: string;
}

export interface VersionHistory {
  file_path: string;
  current_version: number;
  versions: VersionMetadata[];
}

class ApiService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = RUST_CORE_URL;
  }

  // Health check - all services status from Rust core
  async checkHealth(): Promise<HealthStatus> {
    try {
      const res = await fetch(`${this.baseUrl}/api/health`);
      if (!res.ok) throw new Error('Health check failed');
      return res.json();
    } catch {
      return {
        status: 'offline',
        version: 'unknown',
        services: {
          rust_core: false,
          main_agent: false,
          maintenance_agent: false,
          embeddings: false,
        },
      };
    }
  }

  // Project Operations
  async listProjects(): Promise<Project[]> {
    const res = await fetch(`${this.baseUrl}/api/projects`);
    if (!res.ok) throw new Error('Failed to fetch projects');
    return res.json();
  }

  async createProject(name: string, description?: string, location?: string): Promise<Project> {
    const res = await fetch(`${this.baseUrl}/api/projects`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, description, location }),
    });
    if (!res.ok) throw new Error('Failed to create project');
    return res.json();
  }

  async getProject(id: string): Promise<Project> {
    const res = await fetch(`${this.baseUrl}/api/projects/${id}`);
    if (!res.ok) throw new Error('Failed to fetch project');
    return res.json();
  }

  // File Operations - all handled by Rust core
  async listFiles(projectId: string): Promise<FileItem[]> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/files`);
    if (!res.ok) throw new Error('Failed to fetch files');
    return res.json();
  }

  async getFileContent(projectId: string, path: string): Promise<string> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/files/${encodeURIComponent(path)}`);
    if (!res.ok) throw new Error('Failed to fetch file content');
    return res.text();
  }

  async writeFile(projectId: string, path: string, content: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/files/${encodeURIComponent(path)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'text/plain' },
      body: content,
    });
    if (!res.ok) throw new Error('Failed to write file');
  }

  // Version Tracking Operations
  async listFileVersions(projectId: string, filePath: string): Promise<VersionHistory> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/versions/${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error('Failed to fetch version history');
    return res.json();
  }

  async getFileVersion(projectId: string, filePath: string, version: number): Promise<VersionEntry> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/version/${version}/${encodeURIComponent(filePath)}`);
    if (!res.ok) throw new Error('Failed to fetch version content');
    return res.json();
  }

  async restoreFileVersion(projectId: string, filePath: string, version: number): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/restore/${version}/${encodeURIComponent(filePath)}`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to restore version');
  }

  // Chat - Rust core proxies to Python agent service
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const res = await fetch(`${this.baseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || 'Failed to send message');
    }
    return res.json();
  }

  // Chat with streaming using Server-Sent Events
  async sendMessageStream(
    request: ChatRequest,
    onEvent: (event: StreamEvent) => void,
    onComplete: (response: ChatResponse) => void,
    onError: (error: Error) => void
  ): Promise<void> {
    try {
      const res = await fetch(`${this.baseUrl}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('No response body');
      }

      let buffer = '';
      let toolCalls: ToolCall[] = [];
      let finalResponse = '';
      let messageId = '';

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const event = JSON.parse(data) as StreamEvent;
              onEvent(event);

              // Track data for final response
              if (event.type === 'tool_call') {
                toolCalls.push({
                  name: event.name!,
                  arguments: event.arguments || {},
                });
              } else if (event.type === 'response') {
                finalResponse = event.content || '';
              } else if (event.type === 'done') {
                messageId = event.message_id || '';
              }
            } catch (e) {
              console.error('Failed to parse SSE event:', e, data);
            }
          }
        }
      }

      // Call completion callback
      onComplete({
        response: finalResponse,
        tool_calls: toolCalls.length > 0 ? toolCalls : undefined,
        message_id: messageId || `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      });
    } catch (error) {
      onError(error instanceof Error ? error : new Error('Unknown error'));
    }
  }

  // WebSocket connection for real-time chat
  createWebSocket(): WebSocket {
    const wsUrl = this.baseUrl.replace('http', 'ws');
    return new WebSocket(`${wsUrl}/ws`);
  }

  // Timeline - handled by Rust core
  async getTimeline(projectId: string): Promise<TimelineEntry[]> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/timeline`);
    if (!res.ok) throw new Error('Failed to fetch timeline');
    return res.json();
  }

  // Maintenance Suggestions - Rust core coordinates with maintenance service
  async getSuggestions(projectId: string): Promise<Suggestion[]> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/suggestions`);
    if (!res.ok) throw new Error('Failed to fetch suggestions');
    return res.json();
  }

  async acceptSuggestion(projectId: string, suggestionId: string): Promise<{ success: boolean; changes?: string[]; error?: string }> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/suggestions/${suggestionId}/accept`, {
      method: 'POST',
    });
    if (!res.ok) {
      const error = await res.json().catch(() => ({ error: 'Failed to accept suggestion' }));
      throw new Error(error.error || 'Failed to accept suggestion');
    }
    return res.json();
  }

  async dismissSuggestion(projectId: string, suggestionId: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/suggestions/${suggestionId}/dismiss`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to dismiss suggestion');
  }

  async triggerMaintenance(projectId: string, customMessage?: string): Promise<any> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/maintenance/trigger`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ custom_message: customMessage }),
    });
    if (!res.ok) throw new Error('Failed to trigger maintenance');
    return res.json();
  }

  // Settings - managed by Rust core
  async getSettings(): Promise<Settings> {
    try {
      const res = await fetch(`${this.baseUrl}/api/settings`);
      if (!res.ok) throw new Error('Failed to fetch settings');
      return res.json();
    } catch {
      // Return defaults if settings endpoint not available
      return {
        workspace_root: this.getDefaultWorkspaceRoot(),
        ollama_url: 'http://localhost:11434',
        ollama_model: 'gemma:7b',
        theme: 'dark',
      };
    }
  }

  async updateSettings(settings: Partial<Settings>): Promise<Settings> {
    const res = await fetch(`${this.baseUrl}/api/settings`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(settings),
    });
    if (!res.ok) throw new Error('Failed to update settings');
    return res.json();
  }

  private getDefaultWorkspaceRoot(): string {
    // Platform-specific default paths (placeholder for display)
    if (typeof window !== 'undefined') {
      const userAgent = window.navigator.userAgent.toLowerCase();
      if (userAgent.includes('win')) {
        // Display placeholder - actual path resolved by Rust backend
        return 'C:\\Users\\<username>\\.agent-workspace';
      }
    }
    return '~/.agent-workspace';
  }

  // SSE for real-time suggestion updates
  subscribeSuggestions(projectId: string, onSuggestion: (data: any) => void): () => void {
    const eventSource = new EventSource(`${this.baseUrl}/api/projects/${projectId}/suggestions/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onSuggestion(data);
      } catch (err) {
        console.error('Failed to parse SSE data:', err);
      }
    };
    
    eventSource.onerror = (err) => {
      console.error('SSE error:', err);
      eventSource.close();
    };
    
    // Return cleanup function
    return () => {
      eventSource.close();
    };
  }

  // Prompts API (local storage for now, can be moved to backend later)
  async listPrompts(projectId: string): Promise<Prompt[]> {
    const key = `prompts_${projectId}`;
    const stored = localStorage.getItem(key);
    if (!stored) return [];
    
    try {
      const prompts: PromptData[] = JSON.parse(stored);
      return prompts.map((p) => ({
        ...p,
        createdAt: new Date(p.createdAt),
        updatedAt: new Date(p.updatedAt),
      }));
    } catch {
      return [];
    }
  }

  async createPrompt(projectId: string, name: string, content: string): Promise<Prompt> {
    const prompts = await this.listPrompts(projectId);
    const newPrompt: Prompt = {
      id: `prompt-${Date.now()}`,
      name,
      content,
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    
    const updated = [...prompts, newPrompt];
    const key = `prompts_${projectId}`;
    const promptData: PromptData[] = updated.map(p => ({
      ...p,
      createdAt: p.createdAt.toISOString(),
      updatedAt: p.updatedAt.toISOString(),
    }));
    localStorage.setItem(key, JSON.stringify(promptData));
    
    return newPrompt;
  }

  async updatePrompt(projectId: string, promptId: string, name: string, content: string): Promise<void> {
    const prompts = await this.listPrompts(projectId);
    const updated = prompts.map(p =>
      p.id === promptId
        ? { ...p, name, content, updatedAt: new Date() }
        : p
    );
    
    const key = `prompts_${projectId}`;
    const promptData: PromptData[] = updated.map(p => ({
      ...p,
      createdAt: p.createdAt.toISOString(),
      updatedAt: p.updatedAt.toISOString(),
    }));
    localStorage.setItem(key, JSON.stringify(promptData));
  }

  async deletePrompt(projectId: string, promptId: string): Promise<void> {
    const prompts = await this.listPrompts(projectId);
    const updated = prompts.filter(p => p.id !== promptId);
    
    const key = `prompts_${projectId}`;
    const promptData: PromptData[] = updated.map(p => ({
      ...p,
      createdAt: p.createdAt.toISOString(),
      updatedAt: p.updatedAt.toISOString(),
    }));
    localStorage.setItem(key, JSON.stringify(promptData));
  }
}

// Export singleton instance
export const api = new ApiService();
