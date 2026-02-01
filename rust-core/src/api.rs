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

/// Health check endpoint
pub async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        services: ServiceStatus {
            rust_core: true,
            main_agent: false,
            maintenance_agent: false,
            embeddings: false,
        },
    })
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
