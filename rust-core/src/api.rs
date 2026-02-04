use axum::{
    extract::{Path, State},
    http::StatusCode,
    Json,
    response::{sse::{Event, Sse}, IntoResponse, Response},
    body::Body,
};
use std::sync::Arc;
use tokio::sync::RwLock;
use chrono::Utc;
use uuid::Uuid;
use futures::stream::{Stream, StreamExt};
use std::convert::Infallible;

use crate::models::*;
use crate::AppState;

const AGENT_SERVICE_URL: &str = "http://localhost:8001";
const MAINTENANCE_SERVICE_URL: &str = "http://localhost:8002";
const EMBEDDINGS_SERVICE_URL: &str = "http://localhost:8003";

/// Health check endpoint - checks all services
pub async fn health_check() -> Json<HealthResponse> {
    let client = reqwest::Client::new();
    
    // Check Python services availability
    let main_agent = client.get(&format!("{}/health", AGENT_SERVICE_URL))
        .send().await.map(|r| r.status().is_success()).unwrap_or(false);
    
    let maintenance_agent = client.get(&format!("{}/health", MAINTENANCE_SERVICE_URL))
        .send().await.map(|r| r.status().is_success()).unwrap_or(false);
    
    let embeddings = client.get(&format!("{}/health", EMBEDDINGS_SERVICE_URL))
        .send().await.map(|r| r.status().is_success()).unwrap_or(false);
    
    Json(HealthResponse {
        status: "ok".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        services: ServiceStatus {
            rust_core: true,
            main_agent,
            maintenance_agent,
            embeddings,
        },
    })
}

/// Chat endpoint - proxies to Python agent service
pub async fn chat(
    State(state): State<Arc<RwLock<AppState>>>,
    Json(request): Json<ChatRequest>,
) -> Result<Json<ChatResponse>, StatusCode> {
    let client = reqwest::Client::new();
    
    // Get workspace root from settings
    let workspace_root = {
        let state = state.read().await;
        state.settings.workspace_root.clone()
    };
    
    // Forward request to Python agent service with workspace context
    let agent_request = AgentChatRequest {
        message: request.message.clone(),
        context: request.context.clone(),
        tools: request.tools.clone(),
        project_id: request.project_id.clone(),
        workspace_root: Some(workspace_root),
        chat_history: request.chat_history.clone(),
    };
    
    match client
        .post(&format!("{}/agent/chat", AGENT_SERVICE_URL))
        .json(&agent_request)
        .send()
        .await
    {
        Ok(response) => {
            let status = response.status();
            if status.is_success() {
                match response.json::<AgentChatResponse>().await {
                    Ok(agent_response) => {
                        // Log the interaction
                        let state = state.read().await;
                        if let Some(project_id) = &request.project_id {
                            state.session.log_message(project_id, &request.message, &agent_response.response);
                        }
                        
                        Ok(Json(ChatResponse {
                            response: agent_response.response,
                            tool_calls: agent_response.tool_calls,
                            message_id: agent_response.message_id,
                        }))
                    }
                    Err(e) => {
                        tracing::error!("Failed to parse agent response: {}", e);
                        Err(StatusCode::INTERNAL_SERVER_ERROR)
                    }
                }
            } else {
                // Agent service returned an error - get the error message
                let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                tracing::error!("Agent service error (status {}): {}", status, error_text);
                Err(StatusCode::BAD_GATEWAY)
            }
        }
        Err(e) => {
            // Agent service not available
            tracing::error!("Failed to connect to agent service: {}", e);
            Ok(Json(ChatResponse {
                response: "I'm sorry, but I'm currently unable to process your request. The AI agent service is not available. Please ensure Ollama is running and try again.".to_string(),
                tool_calls: None,
                message_id: Uuid::new_v4().to_string(),
            }))
        }
    }
}

/// Chat streaming endpoint - proxies to Python agent service with SSE
pub async fn chat_stream(
    State(state): State<Arc<RwLock<AppState>>>,
    Json(request): Json<ChatRequest>,
) -> Sse<impl Stream<Item = Result<Event, Infallible>>> {
    let workspace_root = {
        let state = state.read().await;
        state.settings.workspace_root.clone()
    };
    
    // Forward request to Python agent service
    let agent_request = AgentChatRequest {
        message: request.message.clone(),
        context: request.context.clone(),
        tools: request.tools.clone(),
        project_id: request.project_id.clone(),
        workspace_root: Some(workspace_root),
        chat_history: request.chat_history.clone(),
    };
    
    let stream = async_stream::stream! {
        let client = reqwest::Client::new();
        
        match client
            .post(&format!("{}/agent/chat/stream", AGENT_SERVICE_URL))
            .json(&agent_request)
            .send()
            .await
        {
            Ok(response) => {
                let mut stream = response.bytes_stream();
                
                while let Some(chunk) = stream.next().await {
                    match chunk {
                        Ok(bytes) => {
                            if let Ok(text) = String::from_utf8(bytes.to_vec()) {
                                // Forward SSE events directly
                                for line in text.lines() {
                                    if line.starts_with("data: ") {
                                        let data = &line[6..];
                                        yield Ok(Event::default().data(data));
                                    }
                                }
                            }
                        }
                        Err(e) => {
                            tracing::error!("Stream error: {}", e);
                            yield Ok(Event::default().data(format!("{{\"type\":\"error\",\"message\":\"{}\"}}", e)));
                            break;
                        }
                    }
                }
            }
            Err(e) => {
                tracing::error!("Failed to connect to agent service: {}", e);
                yield Ok(Event::default().data(format!("{{\"type\":\"error\",\"message\":\"Agent service unavailable: {}\"}}", e)));
            }
        }
    };
    
    Sse::new(stream)
}

/// Get settings
pub async fn get_settings(
    State(state): State<Arc<RwLock<AppState>>>,
) -> Json<Settings> {
    let state = state.read().await;
    Json(state.settings.clone())
}

/// Update settings
pub async fn update_settings(
    State(state): State<Arc<RwLock<AppState>>>,
    Json(new_settings): Json<Settings>,
) -> Result<Json<Settings>, StatusCode> {
    let mut state = state.write().await;
    state.settings = new_settings.clone();
    // TODO: Persist settings to disk
    Ok(Json(new_settings))
}

/// List all projects
pub async fn list_projects(
    State(state): State<Arc<RwLock<AppState>>>,
) -> Result<Json<Vec<Project>>, StatusCode> {
    let state = state.read().await;
    match state.workspace.list_projects() {
        Ok(projects) => Ok(Json(projects)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

/// Create a new project
pub async fn create_project(
    State(state): State<Arc<RwLock<AppState>>>,
    Json(payload): Json<CreateProjectRequest>,
) -> Result<Json<Project>, StatusCode> {
    let state = state.read().await;
    let project = Project::new(payload.name, payload.description)
        .with_location(payload.location.clone());
    
    match state.workspace.create_project(&project) {
        Ok(_) => Ok(Json(project)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

#[derive(serde::Deserialize)]
pub struct CreateProjectRequest {
    pub name: String,
    pub description: Option<String>,
    pub location: Option<String>,
}

/// Get project by ID
pub async fn get_project(
    State(state): State<Arc<RwLock<AppState>>>,
    Path(id): Path<String>,
) -> Result<Json<Project>, StatusCode> {
    let state = state.read().await;
    match state.workspace.get_project(&id) {
        Ok(Some(project)) => Ok(Json(project)),
        Ok(None) => Err(StatusCode::NOT_FOUND),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

/// List files in project
pub async fn list_files(
    State(state): State<Arc<RwLock<AppState>>>,
    Path(id): Path<String>,
) -> Result<Json<Vec<FileItem>>, StatusCode> {
    let state = state.read().await;
    match state.workspace.list_files(&id) {
        Ok(files) => Ok(Json(files)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

/// Get file content
pub async fn get_file(
    State(state): State<Arc<RwLock<AppState>>>,
    Path((id, path)): Path<(String, String)>,
) -> Result<String, StatusCode> {
    let state = state.read().await;
    match state.workspace.read_file(&id, &path) {
        Ok(content) => Ok(content),
        Err(_) => Err(StatusCode::NOT_FOUND),
    }
}

/// Write file content
pub async fn write_file(
    State(state): State<Arc<RwLock<AppState>>>,
    Path((id, path)): Path<(String, String)>,
    body: String,
) -> Result<StatusCode, StatusCode> {
    let state = state.read().await;
    match state.workspace.write_file(&id, &path, &body) {
        Ok(_) => {
            // Notify maintenance agent of file change (non-blocking)
            let project_id = id.clone();
            let file_path = path.clone();
            tokio::spawn(async move {
                let _ = notify_file_change(&project_id, &file_path, "modified").await;
            });
            
            Ok(StatusCode::OK)
        }
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

/// Notify maintenance agent of file change (best effort, non-blocking)
async fn notify_file_change(
    project_id: &str,
    file_path: &str,
    change_type: &str
) -> Result<(), Box<dyn std::error::Error>> {
    let client = reqwest::Client::new();
    
    // Get workspace path
    let home = std::env::var("USERPROFILE")
        .or_else(|_| std::env::var("HOME"))
        .unwrap_or_else(|_| ".".to_string());
    let workspace_path = format!("{}/.agent-workspace/projects/{}", home, project_id);
    
    // Gather workspace context
    let mut files = Vec::new();
    let mut folders = Vec::new();
    let mut readme_content = None;
    let mut file_content = None;
    
    // Read file content if it's a text file
    let full_file_path = format!("{}/{}", workspace_path, file_path);
    if let Ok(content) = tokio::fs::read_to_string(&full_file_path).await {
        file_content = Some(content);
    }
    
    // Read README if it exists
    let readme_path = format!("{}/README.md", workspace_path);
    if let Ok(content) = tokio::fs::read_to_string(&readme_path).await {
        readme_content = Some(content);
    }
    
    // Scan workspace structure
    if let Ok(mut entries) = tokio::fs::read_dir(&workspace_path).await {
        while let Ok(Some(entry)) = entries.next_entry().await {
            if let Ok(file_type) = entry.file_type().await {
                let name = entry.file_name().to_string_lossy().to_string();
                
                // Skip hidden files/folders
                if name.starts_with('.') {
                    continue;
                }
                
                if file_type.is_dir() {
                    folders.push(name);
                } else {
                    files.push(name);
                }
            }
        }
    }
    
    let _ = client
        .post("http://localhost:8002/maintenance/file-change")
        .json(&serde_json::json!({
            "project_id": project_id,
            "file_path": file_path,
            "change_type": change_type,
            "workspace_path": workspace_path,
            "file_content": file_content,
            "readme_content": readme_content,
            "workspace_structure": {
                "files": files,
                "folders": folders
            }
        }))
        .timeout(std::time::Duration::from_secs(5))
        .send()
        .await;
    Ok(())
}

/// Get project timeline
pub async fn get_timeline(
    State(_state): State<Arc<RwLock<AppState>>>,
    Path(_id): Path<String>,
) -> Json<Vec<TimelineEntry>> {
    // Return mock timeline for now
    Json(vec![
        TimelineEntry {
            id: Uuid::new_v4().to_string(),
            timestamp: Utc::now(),
            title: "Researched authentication patterns".to_string(),
            files: vec![
                FileAction { action: "read".to_string(), path: "strategy.md".to_string() },
                FileAction { action: "write".to_string(), path: "oauth_notes.md".to_string() },
            ],
        },
    ])
}

/// Get maintenance suggestions
pub async fn get_suggestions(
    State(_state): State<Arc<RwLock<AppState>>>,
    Path(project_id): Path<String>,
) -> Json<Vec<Suggestion>> {
    let client = reqwest::Client::new();
    
    match client
        .get(&format!("{}/maintenance/suggestions/{}", MAINTENANCE_SERVICE_URL, project_id))
        .send()
        .await
    {
        Ok(response) if response.status().is_success() => {
            if let Ok(data) = response.json::<serde_json::Value>().await {
                if let Some(suggestions) = data.get("suggestions").and_then(|s| s.as_array()) {
                    let parsed: Vec<Suggestion> = suggestions.iter().filter_map(|s| {
                        let sug_type = s.get("type")?.as_str()?;
                        Some(Suggestion {
                            id: s.get("id")?.as_str()?.to_string(),
                            suggestion_type: match sug_type {
                                "merge" => SuggestionType::Merge,
                                "outdated" => SuggestionType::Outdated,
                                "update" | "organize" | "move" | "modify" => SuggestionType::Update,
                                _ => {
                                    tracing::warn!("Unknown suggestion type: {}", sug_type);
                                    return None;
                                }
                            },
                            title: s.get("title")?.as_str()?.to_string(),
                            description: s.get("description")?.as_str()?.to_string(),
                            affected_files: s.get("affected_files").and_then(|f| {
                                f.as_array().map(|arr| {
                                    arr.iter().filter_map(|v| v.as_str().map(|s| s.to_string())).collect()
                                })
                            }),
                        })
                    }).collect();
                    return Json(parsed);
                }
            }
        }
        _ => {}
    }
    
    // Return empty on error
    Json(vec![])
}

/// Accept a suggestion
pub async fn accept_suggestion(
    Path((_project_id, suggestion_id)): Path<(String, String)>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let client = reqwest::Client::new();
    
    match client
        .post(&format!("{}/maintenance/suggestions/{}/accept", MAINTENANCE_SERVICE_URL, suggestion_id))
        .send()
        .await
    {
        Ok(response) if response.status().is_success() => {
            match response.json::<serde_json::Value>().await {
                Ok(data) => {
                    tracing::info!("Accepted suggestion: {}", suggestion_id);
                    Ok(Json(data))
                }
                Err(e) => {
                    tracing::error!("Failed to parse accept response: {}", e);
                    Err(StatusCode::INTERNAL_SERVER_ERROR)
                }
            }
        }
        Ok(response) if response.status() == 404 => {
            tracing::warn!("Suggestion not found: {}", suggestion_id);
            Err(StatusCode::NOT_FOUND)
        }
        _ => {
            tracing::error!("Failed to accept suggestion: {}", suggestion_id);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Dismiss a suggestion
pub async fn dismiss_suggestion(
    Path((_project_id, suggestion_id)): Path<(String, String)>,
) -> Result<StatusCode, StatusCode> {
    let client = reqwest::Client::new();
    
    match client
        .post(&format!("{}/maintenance/suggestions/{}/dismiss", MAINTENANCE_SERVICE_URL, suggestion_id))
        .send()
        .await
    {
        Ok(response) if response.status().is_success() => {
            tracing::info!("Dismissed suggestion: {}", suggestion_id);
            Ok(StatusCode::OK)
        }
        Ok(response) if response.status() == 404 => {
            tracing::warn!("Suggestion not found: {}", suggestion_id);
            Err(StatusCode::NOT_FOUND)
        }
        _ => {
            tracing::error!("Failed to dismiss suggestion: {}", suggestion_id);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}

/// Trigger maintenance analysis for a project
pub async fn trigger_maintenance(
    State(state): State<Arc<RwLock<AppState>>>,
    Path(project_id): Path<String>,
    Json(body): Json<serde_json::Value>,
) -> Result<Json<serde_json::Value>, StatusCode> {
    let client = reqwest::Client::new();
    
    tracing::info!("Triggering maintenance analysis for project: {}", project_id);
    
    let state = state.read().await;
    
    // Get project to determine workspace path
    let project = match state.workspace.get_project(&project_id) {
        Ok(Some(proj)) => proj,
        Ok(None) => {
            tracing::error!("Project not found: {}", project_id);
            return Err(StatusCode::NOT_FOUND);
        }
        Err(e) => {
            tracing::error!("Failed to get project: {}", e);
            return Err(StatusCode::INTERNAL_SERVER_ERROR);
        }
    };
    
    // Determine project directory
    let workspace_path = if let Some(location) = &project.location {
        location.clone()
    } else {
        // Use default workspace location
        let home = std::env::var("USERPROFILE")
            .or_else(|_| std::env::var("HOME"))
            .unwrap_or_else(|_| ".".to_string());
        format!("{}/.agent-workspace/projects/{}", home, project_id)
    };
    
    // Build request with workspace path and optional custom message
    let mut request_body = serde_json::json!({
        "workspace_path": workspace_path
    });
    
    if let Some(custom_message) = body.get("custom_message") {
        if !custom_message.is_null() {
            request_body["custom_message"] = custom_message.clone();
        }
    }
    
    match client
        .post(&format!("{}/maintenance/trigger/{}", MAINTENANCE_SERVICE_URL, project_id))
        .json(&request_body)
        .send()
        .await
    {
        Ok(response) if response.status().is_success() => {
            match response.json::<serde_json::Value>().await {
                Ok(data) => {
                    tracing::info!("Maintenance analysis completed for project: {}", project_id);
                    Ok(Json(data))
                }
                Err(e) => {
                    tracing::error!("Failed to parse maintenance response: {}", e);
                    Err(StatusCode::INTERNAL_SERVER_ERROR)
                }
            }
        }
        _ => {
            tracing::error!("Failed to trigger maintenance for project: {}", project_id);
            Err(StatusCode::INTERNAL_SERVER_ERROR)
        }
    }
}


/// Stream suggestions via SSE - proxy to maintenance service
pub async fn stream_suggestions(
    Path(project_id): Path<String>,
) -> impl IntoResponse {
    tracing::info!("SSE client connecting for project: {}", project_id);
    
    let url = format!("{}/maintenance/suggestions/stream/{}", MAINTENANCE_SERVICE_URL, project_id);
    let client = reqwest::Client::new();
    
    match client.get(&url).send().await {
        Ok(response) => {
            // Forward the SSE response stream
            let stream = response.bytes_stream();
            
            Response::builder()
                .status(200)
                .header("Content-Type", "text/event-stream")
                .header("Cache-Control", "no-cache")
                .header("Connection", "keep-alive")
                .body(Body::from_stream(stream))
                .unwrap_or_else(|_| Response::new(Body::empty()))
        }
        Err(e) => {
            tracing::error!("Failed to connect to maintenance SSE: {}", e);
            Response::builder()
                .status(StatusCode::INTERNAL_SERVER_ERROR)
                .body(Body::empty())
                .unwrap()
        }
    }
}
