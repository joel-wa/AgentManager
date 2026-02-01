use axum::{
    extract::{Path, State},
    http::StatusCode,
    Json,
};
use std::sync::Arc;
use tokio::sync::RwLock;
use chrono::Utc;
use uuid::Uuid;

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
    
    // Forward request to Python agent service
    let agent_request = AgentChatRequest {
        message: request.message.clone(),
        context: request.context.clone(),
        tools: request.tools.clone(),
    };
    
    match client
        .post(&format!("{}/agent/chat", AGENT_SERVICE_URL))
        .json(&agent_request)
        .send()
        .await
    {
        Ok(response) => {
            if response.status().is_success() {
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
                    Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
                }
            } else {
                // Agent service returned an error
                Err(StatusCode::BAD_GATEWAY)
            }
        }
        Err(_) => {
            // Agent service not available - return a fallback response
            Ok(Json(ChatResponse {
                response: "I'm sorry, but I'm currently unable to process your request. The AI agent service is not available. Please ensure Ollama is running and try again.".to_string(),
                tool_calls: None,
                message_id: Uuid::new_v4().to_string(),
            }))
        }
    }
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
    let project = Project::new(payload.name, payload.description);
    
    match state.workspace.create_project(&project) {
        Ok(_) => Ok(Json(project)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

#[derive(serde::Deserialize)]
pub struct CreateProjectRequest {
    pub name: String,
    pub description: Option<String>,
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
        Ok(_) => Ok(StatusCode::OK),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
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
    Path(_id): Path<String>,
) -> Json<Vec<Suggestion>> {
    // Return mock suggestions for now
    Json(vec![
        Suggestion {
            id: Uuid::new_v4().to_string(),
            suggestion_type: SuggestionType::Merge,
            title: "Consolidate similar files".to_string(),
            description: "Found 3 files with overlapping content".to_string(),
            affected_files: Some(vec![
                "notes/nn_basics.md".to_string(),
                "research/neural_nets.md".to_string(),
            ]),
        },
    ])
}

/// Accept a suggestion
pub async fn accept_suggestion(
    Path((_project_id, suggestion_id)): Path<(String, String)>,
) -> Result<StatusCode, StatusCode> {
    // TODO: Implement suggestion acceptance via maintenance service
    tracing::info!("Accepting suggestion: {}", suggestion_id);
    Ok(StatusCode::OK)
}

/// Dismiss a suggestion
pub async fn dismiss_suggestion(
    Path((_project_id, suggestion_id)): Path<(String, String)>,
) -> Result<StatusCode, StatusCode> {
    // TODO: Implement suggestion dismissal
    tracing::info!("Dismissing suggestion: {}", suggestion_id);
    Ok(StatusCode::OK)
}
