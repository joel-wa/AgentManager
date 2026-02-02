/**
 * API Service - Handles communication with Rust Core backend
 * All requests go through Rust Core (port 8000) which coordinates with Python services
 */

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

  async acceptSuggestion(projectId: string, suggestionId: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/suggestions/${suggestionId}/accept`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to accept suggestion');
  }

  async dismissSuggestion(projectId: string, suggestionId: string): Promise<void> {
    const res = await fetch(`${this.baseUrl}/api/projects/${projectId}/suggestions/${suggestionId}/dismiss`, {
      method: 'POST',
    });
    if (!res.ok) throw new Error('Failed to dismiss suggestion');
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
}

// Export singleton instance
export const api = new ApiService();
