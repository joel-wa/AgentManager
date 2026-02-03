use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

/// Project metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Project {
    pub id: String,
    pub name: String,
    pub description: Option<String>,
    pub created_at: DateTime<Utc>,
    pub last_accessed: DateTime<Utc>,
    /// Custom location for project files (if not in default workspace)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub location: Option<String>,
}

impl Project {
    pub fn new(name: String, description: Option<String>) -> Self {
        let now = Utc::now();
        Self {
            id: Uuid::new_v4().to_string(),
            name,
            description,
            created_at: now,
            last_accessed: now,
            location: None,
        }
    }
    
    pub fn with_location(mut self, location: Option<String>) -> Self {
        self.location = location;
        self
    }
}

/// Chat message
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: String,
    pub role: MessageRole,
    pub content: String,
    pub timestamp: DateTime<Utc>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_activity: Option<Vec<ToolActivity>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum MessageRole {
    User,
    Assistant,
    System,
}

/// Tool activity record
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolActivity {
    #[serde(rename = "type")]
    pub activity_type: ToolType,
    pub description: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub file_path: Option<String>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ToolType {
    Search,
    Read,
    Write,
    Execute,
}

/// Timeline entry
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TimelineEntry {
    pub id: String,
    pub timestamp: DateTime<Utc>,
    pub title: String,
    pub files: Vec<FileAction>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileAction {
    pub action: String,
    pub path: String,
}

/// Maintenance suggestion
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Suggestion {
    pub id: String,
    #[serde(rename = "type")]
    pub suggestion_type: SuggestionType,
    pub title: String,
    pub description: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub affected_files: Option<Vec<String>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum SuggestionType {
    Merge,
    Outdated,
    Update,
}

/// File item for directory listing
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileItem {
    pub name: String,
    #[serde(rename = "type")]
    pub file_type: FileType,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub extension: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub children: Option<Vec<FileItem>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub summary: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum FileType {
    File,
    Folder,
}

/// WebSocket messages
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum WsMessage {
    Chat { project_id: String, content: String },
    ChatResponse { message: Message },
    ToolActivity { activity: ToolActivity },
    Error { message: String },
}

/// Chat request from frontend
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatRequest {
    pub message: String,
    pub context: Option<String>,
    pub tools: Vec<String>,
    pub project_id: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub chat_history: Option<Vec<HistoryMessage>>,
}

/// Simple history message for context
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HistoryMessage {
    pub role: String,
    pub content: String,
}

/// Chat response to frontend
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatResponse {
    pub response: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_calls: Option<Vec<ToolCall>>,
    pub message_id: String,
}

/// Agent chat request (to Python service)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentChatRequest {
    pub message: String,
    pub context: Option<String>,
    pub tools: Vec<String>,
    pub project_id: Option<String>,
    pub workspace_root: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub chat_history: Option<Vec<HistoryMessage>>,
}

/// Agent chat response (from Python service)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentChatResponse {
    pub response: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub tool_calls: Option<Vec<ToolCall>>,
    pub message_id: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolCall {
    pub name: String,
    pub arguments: serde_json::Value,
}

/// Health check response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
    pub services: ServiceStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServiceStatus {
    pub rust_core: bool,
    pub main_agent: bool,
    pub maintenance_agent: bool,
    pub embeddings: bool,
}

/// Application settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub workspace_root: String,
    pub ollama_url: String,
    pub ollama_model: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub maintenance_model: Option<String>,
    pub theme: String,
}

impl Default for Settings {
    fn default() -> Self {
        Self {
            workspace_root: default_workspace_root(),
            ollama_url: "http://localhost:11434".to_string(),
            ollama_model: "gemma:7b".to_string(),
            maintenance_model: Some("gemma:7b".to_string()),
            theme: "dark".to_string(),
        }
    }
}

fn default_workspace_root() -> String {
    dirs::home_dir()
        .map(|h| h.join(".agent-workspace").to_string_lossy().to_string())
        .unwrap_or_else(|| {
            if cfg!(windows) {
                "C:\\Users\\.agent-workspace".to_string()
            } else {
                "~/.agent-workspace".to_string()
            }
        })
}
